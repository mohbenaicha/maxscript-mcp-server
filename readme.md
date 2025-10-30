This is an MCP server implementation for 3DS Max script, allowing integration with your coding agent to give it specific context. 
This is especially useful since MaxScript is a niche language and most coding agents do not have much knowledge about it, and for agents without internet retrieval capabilities.

# 1. Env setup
```
conda create -n max-mcp-env python=3.12 -y 
conda activate max-mcp-env
pip install -r requirements.txt
```
The requirements are right but you can experiement with slightly newer/older version of packages if you run into any issues

# 2. Run server
```python mcp_server.py```
Note: this will download the sentence transformer model needed to embed your agent's queries - it's about 80mb in size. The model is downloaded once to ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2.
Optional: add host and port arguments `--mcp-port`, `--mcp-host`, defaults to `127.0.0.1:9000`

# 3. Setup VSCode MCP Server Connection
- Add: MCP Server (on your VS Code editor, `CTRL+SHIFT+P` and select `MCP: Add Server`)
- Set URL to: `http://localhost:9000/sse`
- Enter a name for the mcp server connection and set scope (for accessing from workspace or globally - all projects)
- check output to make sure the following logs are present:
```
2025-10-30 15:09:07.309 [info] 405 status sending message to http://localhost:9000/sse, will attempt to fall back to legacy SSE
2025-10-30 15:09:07.318 [info] Discovered 7 tools
```
- A mcp.json is created in the .vscode folder with the server connection details, which also can be manually edited 
- You should not be able to tag the maxscript mcp server in your agent's chat by using # and the name you provided


Future plans for this project:
1. Add an listener to 3DS Max to provide scene context to the mcp server on request