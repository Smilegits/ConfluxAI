---
type: community
members: 23
---

# ChromaDB & Embeddings

**Members:** 23 nodes

## Members
- [[.__init__()_3]] - code - ingestion/pipeline.py
- [[._process()]] - code - ingestion/pipeline.py
- [[._remove_source()]] - code - ingestion/pipeline.py
- [[.delete_source()]] - code - ingestion/pipeline.py
- [[.ingest_file()]] - code - ingestion/pipeline.py
- [[.ingest_text()]] - code - ingestion/pipeline.py
- [[.ingest_url()]] - code - ingestion/pipeline.py
- [[.list_sources()]] - code - ingestion/pipeline.py
- [[.total_chunks()]] - code - ingestion/pipeline.py
- [[ChromaDB Vector Store]] - rationale - ingestion/pipeline.py
- [[Clear v1 chunks (no source_hash) so a fresh ingest produces a consistent corpus.]] - rationale - ingestion/pipeline.py
- [[Embed a batch of texts using the configured provider.]] - rationale - ingestion/pipeline.py
- [[Ingestion pipeline — orchestrates load → chunk → enrich → embed → store. Idemp]] - rationale - ingestion/pipeline.py
- [[IngestionPipeline]] - code - ingestion/pipeline.py
- [[IngestionPipeline._process]] - code - ingestion/pipeline.py
- [[Return enriched text for embedding. chunk.text stays raw (stored as document).]] - rationale - ingestion/pipeline.py
- [[TextLoader]] - code - ingestion/loaders.py
- [[_enrich()]] - code - ingestion/pipeline.py
- [[_get_embed_client()]] - code - ingestion/pipeline.py
- [[_migrate_schema_if_needed()]] - code - ingestion/pipeline.py
- [[get_collection()]] - code - ingestion/pipeline.py
- [[get_embeddings()]] - code - ingestion/pipeline.py
- [[pipeline.py]] - code - ingestion/pipeline.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ChromaDB__Embeddings
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Document Loaders]]
- 4 edges to [[_COMMUNITY_Streamlit UI & App Logic]]
- 3 edges to [[_COMMUNITY_Text Chunker]]
- 3 edges to [[_COMMUNITY_Hybrid Retrieval & Reranking]]
- 1 edge to [[_COMMUNITY_App Entry & Session Init]]
- 1 edge to [[_COMMUNITY_Ingest CLI Pipeline]]

## Top bridge nodes
- [[IngestionPipeline]] - degree 16, connects to 4 communities
- [[get_collection()]] - degree 11, connects to 2 communities
- [[get_embeddings()]] - degree 7, connects to 2 communities
- [[TextLoader]] - degree 4, connects to 1 community
- [[.__init__()_3]] - degree 4, connects to 1 community