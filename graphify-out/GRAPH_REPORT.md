# Graph Report - .  (2026-05-17)

## Corpus Check
- Corpus is ~7,913 words - fits in a single context window. You may not need a graph.

## Summary
- 176 nodes · 297 edges · 14 communities (10 shown, 4 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.73)
- Token cost: 70,819 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Streamlit UI & App Logic|Streamlit UI & App Logic]]
- [[_COMMUNITY_LLM Client & API|LLM Client & API]]
- [[_COMMUNITY_Document Loaders|Document Loaders]]
- [[_COMMUNITY_ChromaDB & Embeddings|ChromaDB & Embeddings]]
- [[_COMMUNITY_Hybrid Retrieval & Reranking|Hybrid Retrieval & Reranking]]
- [[_COMMUNITY_App Entry & Session Init|App Entry & Session Init]]
- [[_COMMUNITY_Text Chunker|Text Chunker]]
- [[_COMMUNITY_Ingest CLI Pipeline|Ingest CLI Pipeline]]
- [[_COMMUNITY_Claude Settings|Claude Settings]]
- [[_COMMUNITY_Local Permissions Config|Local Permissions Config]]
- [[_COMMUNITY_Settings Config|Settings Config]]
- [[_COMMUNITY_Settings Dataclass|Settings Dataclass]]
- [[_COMMUNITY_CLI Entry Point|CLI Entry Point]]

## God Nodes (most connected - your core abstractions)
1. `get_loader()` - 16 edges
2. `IngestionPipeline` - 16 edges
3. `LLMClient` - 12 edges
4. `RawDocument` - 11 edges
5. `get_collection()` - 11 edges
6. `hybrid_retrieve()` - 11 edges
7. `Orchestrator` - 9 edges
8. `settings singleton` - 9 edges
9. `SessionStore` - 8 edges
10. `SearchResult` - 8 edges

## Surprising Connections (you probably didn't know these)
- `hybrid_retrieve()` --implements--> `Hybrid Retrieval Pattern`  [INFERRED]
  retrieval/engine.py → README.md
- `Orchestrator class` --implements--> `Confidence Gating (skip LLM on NONE)`  [INFERRED]
  orchestrator.py → README.md
- `Orchestrator class` --implements--> `Intent Classification Strategy`  [INFERRED]
  orchestrator.py → README.md
- `Intent Classification Strategy` --rationale_for--> `Orchestrator._classify`  [INFERRED]
  README.md → orchestrator.py
- `IngestionPipeline class` --implements--> `Parent-Child Chunk Pattern`  [INFERRED]
  ingestion/pipeline.py → README.md

## Hyperedges (group relationships)
- **Ingestion Pipeline: load -> chunk -> enrich -> embed -> store** — ingestion_loaders_get_loader, ingestion_chunker_Chunker, ingestion_pipeline_enrich, ingestion_pipeline_get_embeddings, ingestion_pipeline_get_collection [EXTRACTED 1.00]
- **RAG Query Flow: intent -> rewrite -> retrieve -> confidence -> generate** — orchestrator_classify, orchestrator_rewrite, retrieval_engine_hybrid_retrieve, orchestrator_assess_confidence, orchestrator_assemble_context, llm_client_stream_with_history [EXTRACTED 1.00]
- **Hybrid Retrieval: vector + BM25 + RRF + rerank** — retrieval_engine_vector_search, retrieval_engine_keyword_search, retrieval_engine_rrf_fuse, retrieval_engine_rerank [EXTRACTED 1.00]
- **Session Persistence: save/load/delete via MongoDB** — session_store_SessionStore, session_store_serialize_message, session_store_deserialize_message [EXTRACTED 1.00]
- **All modules consuming Settings singleton** — llm_client_LLMClient, orchestrator_assess_confidence, orchestrator_assemble_context, ingestion_chunker_Chunker, ingestion_pipeline_get_embeddings, ingestion_pipeline_get_collection, retrieval_engine_rerank, session_store_SessionStore [EXTRACTED 1.00]

## Communities (14 total, 4 thin omitted)

### Community 0 - "Streamlit UI & App Logic"
Cohesion: 0.09
Nodes (32): init_state function, Streamlit UI (app.py), Confidence Gating (skip LLM on NONE), Intent Classification Strategy, MongoDB Session Persistence, Parent-Child Chunk Pattern, settings singleton, ingest.load_urls (+24 more)

### Community 1 - "LLM Client & API"
Cohesion: 0.13
Nodes (20): Enum, LLMClient, LLM client — wraps OpenAI or Azure OpenAI for sync generation and streaming. Se, _assemble_context(), _assess_confidence(), _build_messages(), Confidence, _extract_sources() (+12 more)

### Community 2 - "Document Loaders"
Cohesion: 0.12
Nodes (16): CSVLoader class, DocxLoader class, ExcelLoader class, PDFLoader class, TxtLoader class, WebLoader class, CSVLoader, DocxLoader (+8 more)

### Community 3 - "ChromaDB & Embeddings"
Cohesion: 0.15
Nodes (13): ChromaDB Vector Store, TextLoader, _enrich(), get_collection(), _get_embed_client(), get_embeddings(), IngestionPipeline, _migrate_schema_if_needed() (+5 more)

### Community 4 - "Hybrid Retrieval & Reranking"
Cohesion: 0.18
Nodes (16): _run_warmup background function, Hybrid Retrieval Pattern, Reciprocal Rank Fusion (RRF), LLMClient class, _crossencoder_rerank(), _get_bm25_index(), _get_llm_rerank_client(), _get_reranker() (+8 more)

### Community 5 - "App Entry & Session Init"
Cohesion: 0.14
Nodes (9): init_state(), _new_session_id(), RAG Chatbot — Streamlit UI  Run with:  streamlit run app.py Ingest data first, MongoDB-backed session store. Persists chat sessions across Streamlit restarts., Convert in-memory message (may have OrchestratorResult) to MongoDB-safe dict., Return {session_id: {name, messages}} sorted by creation time., Upsert session to MongoDB., _serialize_message() (+1 more)

### Community 6 - "Text Chunker"
Cohesion: 0.33
Nodes (5): _approx_tokens(), Chunk, Chunker, _make(), Structure-aware chunker — respects heading boundaries, never splits mid-sentence

### Community 7 - "Ingest CLI Pipeline"
Cohesion: 0.36
Nodes (8): load_files(), load_urls(), _log_result(), main(), _normalize_url(), CLI ingestion script. Reads data/urls.txt (or data/web_urls.txt) and all suppor, Repair common URL entry errors; return clean URL or None if unrecognisable., run()

### Community 8 - "Claude Settings"
Cohesion: 0.5
Nodes (3): statusLine, command, type

## Knowledge Gaps
- **20 isolated node(s):** `Settings`, `type`, `command`, `allow`, `Settings dataclass (config.py)` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IngestionPipeline` connect `ChromaDB & Embeddings` to `Document Loaders`, `App Entry & Session Init`, `Text Chunker`, `Ingest CLI Pipeline`?**
  _High betweenness centrality (0.253) - this node is a cross-community bridge._
- **Why does `init_state()` connect `App Entry & Session Init` to `LLM Client & API`, `ChromaDB & Embeddings`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `get_collection()` connect `ChromaDB & Embeddings` to `Streamlit UI & App Logic`, `Hybrid Retrieval & Reranking`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `get_loader()` (e.g. with `.ingest_url()` and `.ingest_file()`) actually correct?**
  _`get_loader()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `IngestionPipeline` (e.g. with `TextLoader` and `RawDocument`) actually correct?**
  _`IngestionPipeline` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `LLMClient` (e.g. with `Intent` and `Confidence`) actually correct?**
  _`LLMClient` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `RawDocument` (e.g. with `Chunk` and `Chunker`) actually correct?**
  _`RawDocument` has 3 INFERRED edges - model-reasoned connections that need verification._