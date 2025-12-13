
# Application Architecture

This document outlines the architecture of the RAG application, detailing the ingestion, retrieval, and feedback pipelines.

## Mermaid Diagram

```mermaid
---
config:
  layout: dagre
---
flowchart TB
 subgraph Ingestion_Pipeline["Ingestion Pipeline"]
    direction TB
        B{{"File Validation"}}
        A[/"User Uploads Document"/]
        C["Store Raw File (uploads/)"]
        D["Extract Text"]
        E["Chunk Text"]
        F["Generate Chunk Metadata"]
        G["Generate Embeddings"]
        H["Store in Vector DB"]
        I["Store Metadata"]
  end
 subgraph Retrieval_Pipeline["Retrieval Pipeline"]
    direction TB
        K{{"Query Safety Filter"}}
        J[/"User Query"/]
        L{{"Query Validation"}}
        M["Query Embedding Generation"]
        N["Vector Search"]
        O["Re-ranking"]
        P["Assemble & Compress Context"]
        Q["Enhance Context"]
        R["Compose Prompt"]
        S["LLM Invocation (Gemini)"]
        T["Enhance Response"]
        U[/"Return Answer to User"/]
  end
 subgraph Shared_Resources["Shared Storage / DB"]
    direction TB
        V["ChromaDB Vector Store"]
        W["Document Metadata Store (SQLite / MongoDB)"]
  end
 subgraph Feedback_Pipeline["Feedback Pipeline"]
    direction TB
        Y["Store Feedback"]
        X[/"User Feedback"/]
  end
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G & I
    G --> H
    J --> K
    K --> L
    L --> M
    M --> N
    N --> O & V
    O --> P & W
    P --> Q
    Q --> R
    R --> S
    S --> T
    T --> U
    H --> V
    I --> W
    X --> Y
    Y --- O
    U --> X

     B:::validation
     A:::user
     C:::storage
     D:::process
     E:::process
     F:::process
     G:::process
     H:::vector
     I:::metadata
     K:::validation
     J:::user
     L:::validation
     M:::process
     N:::vector
     O:::process
     P:::process
     Q:::process
     R:::process
     S:::llm
     T:::process
     U:::user
     V:::vector
     W:::metadata
     Y:::metadata
     X:::user
    classDef user fill:#FFD966,stroke:#333,stroke-width:1px
    classDef validation fill:#FFABAB,stroke:#333,stroke-width:1px
    classDef storage fill:#A0C4FF,stroke:#333,stroke-width:1px
    classDef process fill:#B5EAEA,stroke:#333,stroke-width:1px
    classDef vector fill:#CDB4DB,stroke:#333,stroke-width:1px
    classDef metadata fill:#FFDAC1,stroke:#333,stroke-width:1px
    classDef llm fill:#FF9CEE,stroke:#333,stroke-width:1px
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
