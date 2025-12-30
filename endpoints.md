# API Endpoints

This document provides a detailed overview of the API endpoints for the application.

## Documents

### `GET /documents`

- **Description:** Retrieves a list of all documents for a given session.
- **Headers:**
    - `session_id` (string, required): The ID of the user session.
- **Response (200 OK):**
    ```json
    {
      "documents": [
        {
          "doc_id": "string",
          "filename": "string",
          "status": "string",
          "quality_score": "integer"
        }
      ]
    }
    ```

### `POST /documents`

- **Description:** Uploads a new document for processing.
- **Headers:**
    - `session_id` (string, required): The ID of the user session.
- **Request:**
    - `file` (file, required): The document to be uploaded.
- **Response (200 OK):**
    ```json
    {
      "doc_id": "string",
      "status": "UPLOADED"
    }
    ```

## Quizzes

### `POST /documents/{doc_id}/quiz`

- **Description:** Creates a new quiz generation job for a specific document.
- **Parameters:**
    - `doc_id` (string, required): The ID of the document.
- **Request Body:**
    ```json
    {
      "difficulty": "string",
      "question_count": "integer",
      "question_types": ["string"],
      "topics": ["string"]
    }
    ```
- **Response (200 OK):**
    ```json
    {
      "quiz_id": "string",
      "status": "GENERATING"
    }
    ```

### `GET /quiz/{quiz_id}/status`

- **Description:** Retrieves the status of a quiz generation job.
- **Parameters:**
    - `quiz_id` (string, required): The ID of the quiz.
- **Response (200 OK):**
    ```json
    {
      "quiz_id": "string",
      "status": "string",
      "questions": []
    }
    ```

## Flashcards

### `POST /documents/{doc_id}/flashcards`

- **Description:** Creates a new flashcard generation job for a specific document.
- **Parameters:**
    - `doc_id` (string, required): The ID of the document.
- **Request Body:**
    ```json
    {
      "count": "integer"
    }
    ```
- **Response (200 OK):**
    ```json
    {
      "flashcards_id": "string",
      "status": "GENERATING"
    }
    ```

### `GET /flashcards/{flashcards_id}/status`

- **Description:** Retrieves the status of a flashcard generation job.
- **Parameters:**
    - `flashcards_id` (string, required): The ID of the flashcards.
- **Response (200 OK):**
    ```json
    {
      "flashcards_id": "string",
      "status": "string",
      "flashcards": []
    }
    ```
