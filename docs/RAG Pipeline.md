##### **RAG PIPELINE TOTAL OVERVIEW**





**Short overview**

This should be a python code build, that can automatically take documents from personal/business OneDrive, make chunkings and embeddings to then upload to vector database inside Supabase



The code should detect new documents being uploaded (in a specific company folder with subfolders and structure) and update the vector database dynamically





**Tech Stack**

Onedrive API (msgraph-sdk)

Docling (chunking and translation to Supabase)

Supabase (document database)

pgvector (make the database searchable)



Pydantic (orchestrator)





**Thoughts to take into account**

This is the foundational PHASE 1 in the chain to built a company specific AI RAG Agent to be used by small company teams and CEO's.

