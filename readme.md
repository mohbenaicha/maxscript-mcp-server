This is an **MCP** server implementation for **3DS MaxScript**, allowing integration with your coding agent to give it specific context. 

This is especially useful since:
   - MaxScript is a relatively powerful but niche language and most coding agents have sparse knowledge about it
   - Max is a bit clunky and needs a LOT of scripting
   - A lot of studios still depend on Max heavily in 2025
   - Agents without internet retrieval capabilities now have a localized documentation
   - The documentation is split up into topics making it easier to access specific topics through filtering or semantic search rather than generally scraping an entire page which is what coding agents with internet access do


### The MCP server feature 7 tools:

1. list_documents: List all document IDs in the database with pagination.
2. search_by_tags: Search documentation by tags (each document has 5-10 important tags for easier filter
3. search_language_reference: semantic search the language reference
4. search_docs: semantic search Objects and Interfaces documentation
5. search_tools_and_ui: semantic search Tools and UI
6. search_os_interaction: semantic search OS Interaction
7. search_examples: semantic search Examples

The semantic search tools require **all-MiniLM-L6-v2** which can run fast single-digit millisecond inference on a CPU when called by the agent (ex: it took me ~ 80 seconds to embed every one of 4000 documents, ~ 14K chunks, in the database using all cores - and don't worry, you won't have to do this since the database comes with the codebase)

# 1. Env setup
**VENV:**

```
python3 -m venv max-mcp-env
source max-mcp-env/bin/activate  # or .\max-mcp-env\Scripts\activate on Windows
pip install -r requirements.txt
```

**Conda:**
```
conda create -n max-mcp-env python=3.12 -y 
conda activate max-mcp-env
pip install -r requirements.txt
```
The requirements are tight but you can experiement with slightly newer/older version of packages if you run into any issues

# 2. Run server
```python mcp_server.py```
Note: this will download the sentence transformer model needed to embed your agent's queries - it's about 80mb in size. The model is downloaded once to ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2.
Optional: add host and port arguments `--mcp-port`, `--mcp-host`, defaults to `127.0.0.1:9000`

# 3. Setup VSCode MCP Server Connection
- Add: MCP Server (on your VS Code editor, `CTRL+SHIFT+P` and select `MCP: Add Server`)
- Set URL to: `http://localhost:9000/sse` (adjust for the host/port that you used)
- Enter a name for the mcp server connection (ex: maxscript-mcp-server) and set scope (for accessing from workspace or globally - all projects)
- check output to make sure the following logs are present:
```
2025-10-30 15:09:07.309 [info] 405 status sending message to http://localhost:9000/sse, will attempt to fall back to legacy SSE
2025-10-30 15:09:07.318 [info] Discovered 7 tools
```
- A mcp.json is created in the .vscode folder (if you used the workspace option) with the server connection details, which also can be manually edited 
- You should not be able to tag the maxscript mcp server in your agent's chat by using # (ex: `#maxscript-mcp-server`) and the name you provided


Future plans for this project:
1. Add an listener to 3DS Max to provide scene context to the mcp server on request
