---
type: community
members: 16
---

# App Entry & Session Init

**Members:** 16 nodes

## Members
- [[.__init__()_2]] - code - session_store.py
- [[.delete()]] - code - session_store.py
- [[.load_all()]] - code - session_store.py
- [[.save()]] - code - session_store.py
- [[Convert in-memory message (may have OrchestratorResult) to MongoDB-safe dict.]] - rationale - session_store.py
- [[MongoDB-backed session store. Persists chat sessions across Streamlit restarts.]] - rationale - session_store.py
- [[RAG Chatbot — Streamlit UI  Run with  streamlit run app.py Ingest data first]] - rationale - app.py
- [[Return {session_id {name, messages}} sorted by creation time.]] - rationale - session_store.py
- [[SessionStore]] - code - session_store.py
- [[Upsert session to MongoDB.]] - rationale - session_store.py
- [[_new_session_id()]] - code - app.py
- [[_run_warmup()]] - code - app.py
- [[_serialize_message()]] - code - session_store.py
- [[app.py]] - code - app.py
- [[init_state()]] - code - app.py
- [[session_store.py]] - code - session_store.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/App_Entry__Session_Init
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_LLM Client & API]]
- 1 edge to [[_COMMUNITY_ChromaDB & Embeddings]]

## Top bridge nodes
- [[init_state()]] - degree 6, connects to 2 communities
- [[SessionStore]] - degree 8, connects to 1 community
- [[session_store.py]] - degree 4, connects to 1 community
- [[.load_all()]] - degree 3, connects to 1 community