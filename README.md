
# Retrieval-Augmented Generation (RAG) System

This document provides a technical overview of the RAG system, a FastAPI-based application that leverages large language models (LLMs) to answer questions based on a corpus of documents.

## Overview

The system is designed to be a modular and extensible platform for building and deploying RAG applications. It consists of three main pipelines: an ingestion pipeline for processing and embedding documents, a retrieval pipeline for answering user queries, and a feedback pipeline for collecting user feedback.

## System Architecture

The application is divided into three main layers: the API layer, the pipeline layer, and the storage layer. See `architecture.md` for a detailed diagram and description of the pipelines.

### Ingestion Pipeline

The ingestion pipeline is responsible for processing and embedding documents. It consists of the following steps:

1.  **File Validation:** Validates the uploaded file type, size, and integrity.
2.  **Text Extraction:** Extracts text from the document using the appropriate loader (e.g., `PyPDFLoader` for PDFs, `Docx2txtLoader` for DOCX files).
3.  **Text Chunking:** Splits the extracted text into smaller, overlapping chunks using the `RecursiveCharacterTextSplitter`.
4.  **Metadata Generation:** Generates metadata for each chunk, including the document ID, paragraph ID, and other relevant information.
5.  **Embedding and Storage:** Generates vector embeddings for each chunk and stores them in a ChromaDB vector store.

### Retrieval Pipeline

The retrieval pipeline is responsible for answering user queries. It consists of the following steps:

1.  **Query Validation:** Validates the user's query for length, language, and safety.
2.  **Retrieval:** Retrieves the top-k most relevant text chunks from the vector store based on the user's query.
3.  **Reranking:** Reranks the retrieved chunks using a cross-encoder to improve relevance.
4.  **Context Assembly:** Assembles the context from the reranked chunks.
5.  **Context Compression:** Compresses the context to optimize for the LLM's context window.
6.  **Prompt Composition:** Composes a prompt using the compressed context and the user's query.
7.  **LLM Invocation:** Invokes the LLM to generate a response.
8.  **Response Enhancement:** Enhances the response by adding sources and other relevant information.

### Feedback Pipeline

The feedback pipeline is responsible for collecting user feedback on the quality of the retrieved documents.

## API Reference

### `POST /embed`

Uploads a document for processing and embedding.

**Request:**

```bash
curl -X POST -F "file=@/path/to/your/file.pdf" -H "session_id: <session_id>" http://localhost:3000/embed
```

**Response:**

```json
{
  "filename": "file.pdf",
  "doc_id": "...",
  "num_chunks": 0
}
```

### `POST /retrieve`

Answers a user's query based on the documents in the vector store.

**Request:**

```bash
curl -X POST -H "Content-Type: application/json" -H "session_id: <session_id>" -d '{"query": "your query"}' http://localhost:3000/retrieve
```

**Response:**

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "...",
      "doc_id": "..."
    }
  ]
}
```

### `POST /api/v1/feedback`

Submits feedback on a document.

**Request:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"doc_id": "...", "rating": 1}' http://localhost:3000/api/v1/feedback
```

**Response:**

```json
{
  "status": "success",
  "doc_id": "...",
  "rating": 1
}
```

## Local Development

To set up the project for local development, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/GoogleCloudPlatform/genai-for-marketing
    cd genai-for-marketing
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**

    Create a `.env` file in the root of the project and add your Gemini API key:

    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```

5.  **Run the application:**

    ```bash
    uvicorn src.main:app --host 0.0.0.0 --port 3000
    ```
