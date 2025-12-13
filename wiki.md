
# RAG Application Wiki

This document provides a detailed explanation of the application's architecture, data flow, and key components.

## Core Architecture

The application is a Retrieval-Augmented Generation (RAG) system. It's designed to answer user queries based on a set of documents that it has processed. The architecture is divided into three main pipelines:

1.  **Ingestion Pipeline:** Processes and embeds documents into a vector database.
2.  **Retrieval Pipeline:** Retrieves relevant documents, generates an answer using a Large Language Model (LLM), and returns it to the user.
3.  **Feedback Pipeline:** Collects user feedback to improve retrieval quality.

---

## 1. Ingestion Pipeline (`/embed`)

This pipeline is responsible for taking unstructured documents, processing them, and storing them in a searchable format.

**Endpoint:** `POST /embed`
**Input:** A file (e.g., `.txt`, `.pdf`) and optional JSON metadata.

### Flow of Ingestion:

1.  **File Validation (`validator.py`):**
    *   The uploaded file is validated to ensure it meets certain criteria (e.g., allowed file types, size limits).

2.  **Raw File Storage:**
    *   The original, unprocessed file is saved to the `uploads/` directory. This serves as a backup and for auditing purposes.

3.  **Content Extraction and Chunking (`preprocessor.py`):**
    *   The text content is extracted from the file.
    *   The extracted text is then divided into smaller, more manageable "chunks." This is crucial for generating focused embeddings and providing precise context to the LLM.

4.  **Document Metadata Storage (`metadata_store.py`):**
    *   **Database:** A relational database (SQLite, located at `db/chroma.sqlite3`) is used as the metadata store.
    *   Document-level metadata (e.g., filename, source, user-provided metadata) is saved to this database.

5.  **Chunk Processing (Loop):**
    Each text chunk goes through the following steps:
    *   **Text Preprocessing (`preprocessor.py`):** The text is cleaned and normalized (e.g., removing extra whitespace, standardizing characters).
    *   **Metadata Generation (`metadata_generator.py`):** Chunk-specific metadata is created (e.g., chunk number, position within the document).
    *   **Embedding and Storage (`vector_store.py`):**
        *   **Embedding Model:** A sentence-transformer model is used to convert the cleaned text chunk into a numerical vector (embedding). This vector represents the semantic meaning of the text.
        *   **Vector Database:** **ChromaDB** is used as the vector store (database located at `chroma/chroma.sqlite3`).
        *   The generated embedding and its associated metadata (linking it back to the original document and chunk) are stored in ChromaDB.

---

## 2. Retrieval Pipeline (`/retrieve`)

This pipeline handles user queries, finds relevant information from the ingested documents, and generates a human-like answer.

**Endpoint:** `POST /retrieve`
**Input:** A user query (string) and `k` (the number of chunks to retrieve).

### Flow of Retrieval:

1.  **Query Safety Filter (`safety_filter.py`):**
    *   The incoming query is first scanned for any potentially harmful or inappropriate content.

2.  **Query Validation (`query_validator.py`):**
    *   The query is validated for things like length and format to ensure it's a valid request.

3.  **Retrieval (`vector_store.py`):**
    *   The user's query is converted into an embedding using the same model from the ingestion pipeline.
    *   This query embedding is used to search the **ChromaDB** vector store.
    *   The search finds the `k` most similar text chunks using a similarity search (e.g., cosine similarity), retrieving the chunks whose embeddings are closest to the query embedding.

4.  **Re-ranking (`ranker.py`):**
    *   The initial `k` results from the vector search are re-ranked to improve their relevance to the query. This step can use additional signals like user feedback, document freshness, or other business logic.

5.  **Context Assembling & Compression (`context_assembler.py`, `optimizer.py`):**
    *   The text from the top-ranked chunks is assembled to form the "context."
    *   This context may be compressed or summarized to ensure it fits within the context window of the LLM while retaining the most critical information.

6.  **Context Enhancement (`context_enhancer.py`):**
    *   The assembled context is enhanced, for example, by adding source information or formatting cues.

7.  **Prompt Composition (`prompt_composer.py`):**
    *   A final prompt is constructed for the LLM. This is a carefully crafted template that includes the user's original query and the retrieved context. The prompt templates are located in `src/prompts/`.

8.  **LLM Invocation (`llm_invoker.py`):**
    *   The composed prompt is sent to a Large Language Model (e.g., a model from OpenAI or Google).
    *   The LLM generates an answer to the query based *only* on the context provided.

9.  **Response Enhancement (`response_enhancer.py`):**
    *   The raw response from the LLM is formatted.
    *   Crucially, it is enhanced with source attribution, linking the parts of the answer back to the specific documents and chunks that were used as context.

---

## 3. Feedback Pipeline (`/api/v1/feedback`)

This pipeline allows the system to learn from user interactions.

**Endpoint:** `POST /api/v1/feedback`
**Input:** A document ID (`doc_id`) and a rating (e.g., "helpful," "not helpful").

### Flow of Feedback:

1.  **Add Feedback (`metadata_store.py`):**
    *   The feedback (e.g., a rating for a specific document) is recorded in the **metadata store** (the SQLite database at `db/chroma.sqlite3`).
    *   This feedback data can then be used by the **Re-ranking** step (`ranker.py`) in the retrieval pipeline to boost or penalize documents in future searches, creating a continuous improvement loop.
