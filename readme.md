# Env setup
```
conda create -n max-mcp-env python=3.12 -y && conda activate max-mcp-env && pip install fastapi uvicorn sentence-transformers faiss-cpu numpy
```

# 1. Setup the DB (parse + embed + index)
python app.py --setup-db

# 2. Run server
python app.py

# 3. Query
GET http://localhost:8000/search?q=climate+change