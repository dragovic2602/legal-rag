##### **RAG STRATEGIES**



**!Reranking**



Two-stage retrieval (20-50+ candidates -> re-rank to top 5)

Pull more content and reduce it



**!Agentic RAG**

Semantic Search 

&nbsp;- Search chunks



Full Document Receival

&nbsp;- Receive complete documents



**Knowledge Graphs**

Combine vector search with a graph database



Graph Database 

&nbsp;- Stores relationships between the entities

&nbsp;- Interconnected data



**Contextual Retrieval** 

Title in the top of chunks to tell how it relates to the documents





**Query Expansion**

Expand the query to make it more specific (pre-tool hook calls)



**Multi Query RAG**

Generates 3-4 queries based on the request from the user to get more data.



**!Context Aware Chunking** 

Find the natural boundaries in the documents to split in the right places



**Hierarchical RAG**

Store Relationships as metadata 



**Fine Tuned Embeddings**



Sentiment embedding to structure based on the data u have 

Open source models can be trained and run this 



##### **Process** 



Index Process



1. Raw data sources
2. Contextual part from doc
3. Chunking of the part
4. Embedding
5. Vector database







