"""
MCP Server for MaxScript Documentation Search
Provides semantic search and tag-based search over MaxScript documentation.
"""

from typing import List, Dict, Any
import argparse
import sqlite3
import logging
import os
from mcp.server.fastmcp import FastMCP
from utils.search import semantic_search

logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("maxscript-docs")

# Database connection for tag search (use absolute path inside mcp/utils)
DB_PATH = os.path.join(os.path.dirname(__file__), "db", "docs.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()


@mcp.tool()
def search_docs(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search Objects and Interfaces documentation.

    Args:
        q: Search query string
        top_k: Number of top results to return (default: 3)

    Returns:
        List of documents with doc_id and reconstructed full text
    """
    return semantic_search("objects_and_interfaces", q, top_k)


@mcp.tool()
def search_tools_and_ui(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search Tools and UI documentation.

    Args:
        q: Search query string
        top_k: Number of top results to return (default: 3)

    Returns:
        List of documents with doc_id and reconstructed full text
    """
    return semantic_search("tools_and_ui", q, top_k)


@mcp.tool()
def search_examples(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search Examples documentation.

    Args:
        q: Search query string
        top_k: Number of top results to return (default: 3)

    Returns:
        List of documents with doc_id and reconstructed full text
    """
    return semantic_search("examples", q, top_k)


@mcp.tool()
def search_os_interaction(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search OS Interaction documentation.

    Args:
        q: Search query string
        top_k: Number of top results to return (default: 3)

    Returns:
        List of documents with doc_id and reconstructed full text
    """
    return semantic_search("os_interaction", q, top_k)


@mcp.tool()
def search_language_reference(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search Language Reference documentation.

    Args:
        q: Search query string
        top_k: Number of top results to return (default: 3)

    Returns:
        List of documents with doc_id and reconstructed full text
    """
    return semantic_search("language_reference", q, top_k)


@mcp.tool()
def search_by_tags(
    tags: List[str], max_docs: int = 3, match_all: bool = False
) -> List[Dict[str, Any]]:
    """
    Search documentation by tags.

    Args:
        tags: List of tags to search for
        max_docs: Maximum number of documents to return (default: 3)
        match_all: If True, only return docs matching ALL tags; if False, match ANY tag (default: False)

    Returns:
        List of documents with doc_id and reconstructed full text
    """
    placeholders = ",".join("?" for _ in tags)
    if match_all:
        sql = f"""
            SELECT doc_id
            FROM chunks, json_each(tags)
            WHERE json_each.value IN ({placeholders})
            GROUP BY doc_id
            HAVING COUNT(DISTINCT json_each.value) = ?
            LIMIT ?
        """
        cur.execute(sql, (*tags, len(tags), max_docs))
    else:
        sql = f"""
            SELECT DISTINCT doc_id
            FROM chunks, json_each(tags)
            WHERE json_each.value IN ({placeholders})
            LIMIT ?
        """
        cur.execute(sql, (*tags, max_docs))

    doc_ids = [row[0] for row in cur.fetchall()]

    # Fetch and reconstruct full docs
    results = []
    for doc_id in doc_ids:
        cur.execute(
            "SELECT chunk_id, text FROM chunks WHERE doc_id=? ORDER BY chunk_id",
            (doc_id,),
        )
        chunks = cur.fetchall()
        full_text = "\n".join([c[1] for c in chunks])
        results.append({"doc_id": doc_id, "text": full_text})

    return results


@mcp.tool()
def list_documents(offset: int = 0, limit: int = 100) -> Dict[str, List[str]]:
    """
    List all document IDs in the database with pagination.

    Args:
        offset: Pagination offset (default: 0)
        limit: Maximum number of documents to return (default: 100)

    Returns:
        Dictionary with 'documents' key containing list of document IDs
    """
    # Safety check
    cur.execute("SELECT DISTINCT doc_id FROM chunks LIMIT ? OFFSET ?", (limit, offset))
    docs = [row[0] for row in cur.fetchall()]
    return {"documents": docs}


def main():
    parser = argparse.ArgumentParser(
        description="MCP server for MaxScript Documentation"
    )
    parser.add_argument(
        "--mcp-host",
        type=str,
        default="127.0.0.1",
        help="Host to run MCP server on (only used for sse), default: 127.0.0.1",
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=9000,
        help="Port to run MCP server on (only used for sse), default: 8081",
    )
    args = parser.parse_args()

    log_level = logging.INFO
    logging.basicConfig(level=log_level)
    logging.getLogger().setLevel(log_level)

    # Configure MCP settings
    mcp.settings.log_level = "INFO"
    mcp.settings.host = args.mcp_host
    mcp.settings.port = args.mcp_port

    logger.info(
        f"Starting MCP server on http://{mcp.settings.host}:{mcp.settings.port}/sse"
    )
    logger.info(f"Using transport: SSE")
    logger.info(f"Database: docs.db")
    logger.info(f"Index: index.faiss")
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
