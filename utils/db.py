import os, re, sqlite3, faiss, numpy as np, json
from sentence_transformers import SentenceTransformer

# Use absolute paths under the mcp/utils folder so server can find them regardless of CWD
BASE_UTILS = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_UTILS, "docs.db")
INDEX_PATH = os.path.join(BASE_UTILS, "index.faiss")

EMBED_MODEL = "all-MiniLM-L6-v2"


def build_db(args):
    model = SentenceTransformer(EMBED_MODEL)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute(
        """CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        doc_id TEXT,
        chunk_id INTEGER,
        text TEXT,
        tags TEXT
    )"""
    )

    DOCS_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", args.dir_name, "markdown"
    )
    PARSED_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", args.dir_name, "parsed"
    )
    embeddings = []
    row_ids = []  # Track database row IDs

    for fname in os.listdir(DOCS_DIR):
        if not fname.endswith(".md"):
            continue
        doc_id = os.path.splitext(fname)[0]

        # read markdown text
        text = open(os.path.join(DOCS_DIR, fname), encoding="utf-8").read()

        # Split into ~500-word chunks (preserves words, collapses whitespace)
        words = re.findall(r"\S+", text)
        if len(words) <= 500:
            chunks = [text]
        else:
            chunks = []
            for i in range(0, len(words), 500):
                chunk_words = words[i : i + 500]
                chunks.append(" ".join(chunk_words))

        print(f"Indexing {doc_id} with {len(chunks)} chunks ({len(words)} words total).")

        # read corresponding parsed JSON for tags
        parsed_path = os.path.join(PARSED_DIR, doc_id + ".json")
        if os.path.exists(parsed_path):
            with open(parsed_path, encoding="utf-8") as f:
                parsed_json = json.load(f)
            tags = parsed_json.get("keywords", [])
        else:
            tags = []

        tags_json = json.dumps(tags)  # store as JSON array string

        for i, chunk in enumerate(chunks):
            cur.execute(
                "INSERT INTO chunks (category, doc_id, chunk_id, text, tags) VALUES (?, ?, ?, ?, ?)",
                (args.dir_name, doc_id, i, chunk, tags_json),
            )
            row_id = cur.lastrowid  # Get the actual database row ID
            row_ids.append(row_id)
            emb = model.encode([chunk], normalize_embeddings=True)
            embeddings.append(emb)

    conn.commit()
    conn.close()

    # build or update FAISS index with ID mapping
    X = np.vstack(embeddings).astype("float32")
    
    # Load existing index if it exists, otherwise create new
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        # Load existing ID map
        id_map_path = INDEX_PATH.replace('.faiss', '_idmap.npy')
        if os.path.exists(id_map_path):
            existing_ids = np.load(id_map_path).tolist()
        else:
            existing_ids = []
        index.add(X)
        all_ids = existing_ids + row_ids
        np.save(id_map_path, np.array(all_ids))
    else:
        index = faiss.IndexFlatIP(X.shape[1])  # cosine via normalized vectors
        index.add(X)
        id_map_path = INDEX_PATH.replace('.faiss', '_idmap.npy')
        np.save(id_map_path, np.array(row_ids))
    
    faiss.write_index(index, INDEX_PATH)
    print(f"Indexed {len(X)} chunks.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build document database and FAISS index"
    )
    parser.add_argument(
        "--dir-names",
        type=str,
        nargs='+',
        default=['examples', 'language_reference', 'tools_and_ui', 'objects_and_interfaces', 'os_interaction'],
        help="List of data dir names to index (default: all)",
    )
    args = parser.parse_args()
    
    # Delete old DB and index
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(INDEX_PATH):
        os.remove(INDEX_PATH)
    id_map_path = INDEX_PATH.replace('.faiss', '_idmap.npy')
    if os.path.exists(id_map_path):
        os.remove(id_map_path)
    
    # Process each directory
    for dir_name in args.dir_names:
        print(f"\n{'='*60}")
        print(f"Processing category: {dir_name}")
        print('='*60)
        class Args:
            pass
        dir_args = Args()
        dir_args.dir_name = dir_name
        build_db(dir_args)
