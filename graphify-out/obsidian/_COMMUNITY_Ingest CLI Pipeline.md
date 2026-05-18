---
type: community
members: 9
---

# Ingest CLI Pipeline

**Members:** 9 nodes

## Members
- [[CLI ingestion script. Reads dataurls.txt (or dataweb_urls.txt) and all suppor]] - rationale - ingest.py
- [[Repair common URL entry errors; return clean URL or None if unrecognisable.]] - rationale - ingest.py
- [[_log_result()]] - code - ingest.py
- [[_normalize_url()]] - code - ingest.py
- [[ingest.py]] - code - ingest.py
- [[load_files()]] - code - ingest.py
- [[load_urls()]] - code - ingest.py
- [[main()]] - code - ingest.py
- [[run()]] - code - ingest.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Ingest_CLI_Pipeline
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_ChromaDB & Embeddings]]
- 1 edge to [[_COMMUNITY_LLM Client & API]]

## Top bridge nodes
- [[run()]] - degree 5, connects to 2 communities