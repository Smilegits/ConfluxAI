---
source_file: "retrieval/engine.py"
type: "code"
community: "Hybrid Retrieval & Reranking"
location: "L228"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Hybrid_Retrieval__Reranking
---

# hybrid_retrieve()

## Connections
- [[.process()]] - `calls` [INFERRED]
- [[.process_stream()]] - `calls` [INFERRED]
- [[Full pipeline vector + BM25 → RRF → rerank → top results.]] - `rationale_for` [EXTRACTED]
- [[Hybrid Retrieval Pattern]] - `implements` [INFERRED]
- [[Orchestrator.process (sync)]] - `calls` [EXTRACTED]
- [[Orchestrator.process_stream (streaming)]] - `calls` [EXTRACTED]
- [[engine.py]] - `contains` [EXTRACTED]
- [[keyword_search()]] - `calls` [EXTRACTED]
- [[rerank()]] - `calls` [EXTRACTED]
- [[rrf_fuse()]] - `calls` [EXTRACTED]
- [[vector_search()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Hybrid_Retrieval__Reranking