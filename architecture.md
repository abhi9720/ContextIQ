
# Application Architecture

This document outlines the architecture of the RAG application, detailing the ingestion, retrieval, and feedback pipelines.

## Mermaid Diagram

```mermaid
graph TD
    subgraph "Ingestion Pipeline (/embed)"
        direction LR
        A["POST /embed <br> (file, metadata)"] --> B{"embed"};
        B --> C["validate_file"];
        C --> D["save_raw_file"];
        D --> E["extract_and_chunk_file"];
        E --> F["add_document"];
        E --> G{"For each chunk"};
        G --> H["preprocess_text"];
        H --> I["generate_metadata"];
        I --> J["embed_and_store"];
    end

    subgraph "Retrieval Pipeline (/retrieve)"
        direction LR
        K["POST /retrieve <br> (query, k)"] --> L{"retrieve_v1"};
        L --> M["filter_safety"];
        M --> N["validate_query"];
        N --> O["retrieve"];
        O --> P["rerank_results"];
        P --> Q["assemble_context"];
        Q --> R["compress_context"];
        R --> S["enhance_context"];
        S --> T["compose_prompt"];
        T --> U["invoke_llm"];
        U --> V["enhance_response"];
        V --> W["Response <br> (answer, sources)"];
    end

    subgraph "Feedback Pipeline (/api/v1/feedback)"
        direction LR
        X["POST /api/v1/feedback <br> (doc_id, rating)"] --> Y{"feedback_v1"};
        Y --> Z["add_feedback"];
    end
```

## Detailed Flow Descriptions

### Ingestion Pipeline (`/embed`)

The ingestion pipeline processes and stores documents to make them searchable.

1.  **Endpoint:** `POST /embed`
2.  **Input:** A file and optional JSON metadata.
3.  **Flow:**
    *   **Validation:** The uploaded file is validated.
    *   **Storage:** The raw file is saved.
    *   **Processing:** The file is processed to extract text, which is then divided into smaller chunks.
    *   **Metadata:** Document-level metadata is stored.
    *   **Chunk Loop:** Each chunk is individually processed:
        *   **Preprocessing:** The text is cleaned.
        *   **Metadata Generation:** Additional metadata is generated for the chunk.
        *   **Embedding & Storage:** A vector embedding is created from the chunk's text and stored in the vector database along with its metadata.

### Retrieval Pipeline (`/retrieve`)

The retrieval pipeline finds relevant information and generates an answer to a user's query.

1.  **Endpoint:** `POST /retrieve`
2.  **Input:** A user query (`query`) and the number of results to retrieve (`k`).
3.  **Flow:**
    *   **Safety & Validation:** The query is sanitized and validated.
    *   **Retrieval:** The system retrieves the most relevant document chunks from the vector store.
    *   **Ranking:** The retrieved results are re-ranked to improve relevance.
    *   **Context Management:** The text from the top-ranked chunks is assembled, compressed, and enhanced to create a context for the language model.
    *   **Prompting:** A prompt is constructed using the context and the user's query.
    *   **LLM Invocation:** The prompt is sent to a large language model to generate a response.
    *   **Response Formatting:** The final response is enhanced with source information and sent back to the user.

### Feedback Pipeline (`/api/v1/feedback`)

This pipeline collects user feedback to improve the system over time.

1.  **Endpoint:** `POST /api/v1/feedback`
2.  **Input:** A document ID (`doc_id`) and a rating (`rating`).
3.  **Flow:**
    *   The feedback is recorded in the metadata store, which can be used to adjust document rankings in future retrievals.
