import os
import sqlite3
import faiss
import numpy as np
from typing import List, Dict, Any
from collections import defaultdict
from sentence_transformers import SentenceTransformer

# Absolute paths under mcp/utils
BASE_UTILS = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_UTILS, "docs.db")
INDEX_PATH = os.path.join(BASE_UTILS, "index.faiss")
EMBED_MODEL = "all-MiniLM-L6-v2"

model = SentenceTransformer(EMBED_MODEL)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()


def semantic_search(category: str, q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Core semantic search function for a specific category.
    
    Args:
        category: Category to search (e.g., 'examples', 'language_reference')
        q: Search query string
        top_k: Number of top results to return
        
    Returns:
        List of documents with doc_id and reconstructed full text
    """
    index = faiss.read_index(INDEX_PATH)
    # Load ID mapping
    id_map_path = INDEX_PATH.replace('.faiss', '_idmap.npy')
    id_map = np.load(id_map_path)
    
    q_emb = model.encode([q], normalize_embeddings=True).astype("float32")
    D, I = index.search(q_emb, 50)

    doc_scores = defaultdict(float)
    docs = defaultdict(list)

    for i, faiss_idx in enumerate(I[0]):
        distance = D[0][i]
        # Map FAISS index to actual database row ID
        db_row_id = int(id_map[faiss_idx])
        cur.execute(
            "SELECT doc_id, chunk_id, text FROM chunks WHERE id=? AND category=?", 
            (db_row_id, category)
        )
        row = cur.fetchone()
        if row:
            doc_id = row[0]
            docs[doc_id].append((row[1], row[2]))
            doc_scores[doc_id] = max(doc_scores[doc_id], distance)

    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for doc_id, score in sorted_docs:
        chunks = docs[doc_id]
        chunks.sort(key=lambda x: x[0])
        full_text = "\n".join([c[1] for c in chunks])
        results.append({"doc_id": doc_id, "text": full_text})

    return results
