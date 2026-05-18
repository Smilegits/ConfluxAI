---
type: community
members: 32
---

# Streamlit UI & App Logic

**Members:** 32 nodes

## Members
- [[Chunk dataclass]] - code - ingestion/chunker.py
- [[Chunker class]] - code - ingestion/chunker.py
- [[Confidence Gating (skip LLM on NONE)]] - rationale - README.md
- [[Confidence enum]] - code - orchestrator.py
- [[IngestionPipeline class]] - code - ingestion/pipeline.py
- [[Intent Classification Strategy]] - rationale - README.md
- [[Intent enum]] - code - orchestrator.py
- [[LLMClient.generate]] - code - llm_client.py
- [[LLMClient.generate_with_history]] - code - llm_client.py
- [[LLMClient.stream_with_history]] - code - llm_client.py
- [[MongoDB Session Persistence]] - rationale - session_store.py
- [[Orchestrator class]] - code - orchestrator.py
- [[Orchestrator._assemble_context]] - code - orchestrator.py
- [[Orchestrator._assess_confidence]] - code - orchestrator.py
- [[Orchestrator._classify]] - code - orchestrator.py
- [[Orchestrator._rewrite]] - code - orchestrator.py
- [[Orchestrator.process (sync)]] - code - orchestrator.py
- [[Orchestrator.process_stream (streaming)]] - code - orchestrator.py
- [[OrchestratorResult dataclass]] - code - orchestrator.py
- [[Parent-Child Chunk Pattern]] - rationale - README.md
- [[RawDocument dataclass]] - code - ingestion/loaders.py
- [[SearchResult dataclass]] - code - retrieval/engine.py
- [[SessionStore class]] - code - session_store.py
- [[Streamlit UI (app.py)]] - code - app.py
- [[_deserialize_message]] - code - session_store.py
- [[_fast_classify (regex greeting classifier)]] - code - orchestrator.py
- [[_serialize_message]] - code - session_store.py
- [[ingest._normalize_url]] - code - ingest.py
- [[ingest.load_urls]] - code - ingest.py
- [[ingest.run function]] - code - ingest.py
- [[init_state function]] - code - app.py
- [[settings singleton]] - code - config.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Streamlit_UI__App_Logic
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Hybrid Retrieval & Reranking]]
- 4 edges to [[_COMMUNITY_ChromaDB & Embeddings]]
- 1 edge to [[_COMMUNITY_Document Loaders]]

## Top bridge nodes
- [[settings singleton]] - degree 9, connects to 2 communities
- [[IngestionPipeline class]] - degree 6, connects to 2 communities
- [[Orchestrator.process (sync)]] - degree 6, connects to 1 community
- [[Orchestrator.process_stream (streaming)]] - degree 6, connects to 1 community
- [[Chunker class]] - degree 6, connects to 1 community