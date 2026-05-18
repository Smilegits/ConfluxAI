---
type: community
members: 31
---

# LLM Client & API

**Members:** 31 nodes

## Members
- [[.__init__()]] - code - llm_client.py
- [[.__init__()_1]] - code - orchestrator.py
- [[._classify()]] - code - orchestrator.py
- [[._rewrite()]] - code - orchestrator.py
- [[.generate()]] - code - llm_client.py
- [[.generate_with_history()]] - code - llm_client.py
- [[.process()]] - code - orchestrator.py
- [[.process_stream()]] - code - orchestrator.py
- [[.stream_with_history()]] - code - llm_client.py
- [[Confidence]] - code - orchestrator.py
- [[Enum]] - code
- [[Intent]] - code - orchestrator.py
- [[LLM client — wraps OpenAI or Azure OpenAI for sync generation and streaming. Se]] - rationale - llm_client.py
- [[LLMClient]] - code - llm_client.py
- [[Orchestrator]] - code - orchestrator.py
- [[Orchestrator — the brain of the RAG chatbot.  Flow   user message → intent c]] - rationale - orchestrator.py
- [[OrchestratorResult]] - code - orchestrator.py
- [[Reconstruct in-memory message from MongoDB document.]] - rationale - session_store.py
- [[SearchResult]] - code - retrieval/engine.py
- [[Streaming yields str chunks, then a final OrchestratorResult.]] - rationale - orchestrator.py
- [[Sync processing — returns full result.]] - rationale - orchestrator.py
- [[_assemble_context()]] - code - orchestrator.py
- [[_assess_confidence()]] - code - orchestrator.py
- [[_build_messages()]] - code - orchestrator.py
- [[_deserialize_message()]] - code - session_store.py
- [[_extract_sources()]] - code - orchestrator.py
- [[_fast_classify()]] - code - orchestrator.py
- [[_history_text()]] - code - orchestrator.py
- [[llm_client.py]] - code - llm_client.py
- [[orchestrator.py]] - code - orchestrator.py
- [[str]] - code

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/LLM_Client__API
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_App Entry & Session Init]]
- 6 edges to [[_COMMUNITY_Hybrid Retrieval & Reranking]]
- 2 edges to [[_COMMUNITY_Document Loaders]]
- 1 edge to [[_COMMUNITY_Ingest CLI Pipeline]]

## Top bridge nodes
- [[LLMClient]] - degree 12, connects to 2 communities
- [[str]] - degree 5, connects to 2 communities
- [[.process()]] - degree 12, connects to 1 community
- [[.process_stream()]] - degree 12, connects to 1 community
- [[Orchestrator]] - degree 9, connects to 1 community