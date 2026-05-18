---
type: community
members: 17
---

# Hybrid Retrieval & Reranking

**Members:** 17 nodes

## Members
- [[Full pipeline vector + BM25 → RRF → rerank → top results.]] - rationale - retrieval/engine.py
- [[Hybrid Retrieval Pattern]] - rationale - README.md
- [[Hybrid retrieval engine combining   1. Vector search (cosine similarity via Ch]] - rationale - retrieval/engine.py
- [[LLMClient class]] - code - llm_client.py
- [[Reciprocal Rank Fusion (RRF)]] - rationale - README.md
- [[_crossencoder_rerank()]] - code - retrieval/engine.py
- [[_get_bm25_index()]] - code - retrieval/engine.py
- [[_get_llm_rerank_client()]] - code - retrieval/engine.py
- [[_get_reranker()]] - code - retrieval/engine.py
- [[_llm_rerank()]] - code - retrieval/engine.py
- [[_run_warmup background function]] - code - app.py
- [[engine.py]] - code - retrieval/engine.py
- [[hybrid_retrieve()]] - code - retrieval/engine.py
- [[keyword_search()]] - code - retrieval/engine.py
- [[rerank()]] - code - retrieval/engine.py
- [[rrf_fuse()]] - code - retrieval/engine.py
- [[vector_search()]] - code - retrieval/engine.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Hybrid_Retrieval__Reranking
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Streamlit UI & App Logic]]
- 6 edges to [[_COMMUNITY_LLM Client & API]]
- 3 edges to [[_COMMUNITY_ChromaDB & Embeddings]]

## Top bridge nodes
- [[hybrid_retrieve()]] - degree 11, connects to 2 communities
- [[vector_search()]] - degree 5, connects to 2 communities
- [[engine.py]] - degree 12, connects to 1 community
- [[_llm_rerank()]] - degree 5, connects to 1 community
- [[rerank()]] - degree 5, connects to 1 community