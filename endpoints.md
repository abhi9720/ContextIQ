
### API Endpoints and `curl` Examples

Here are the `curl` commands to interact with the various endpoints of your RAG API.

**Note:** These commands assume the server is running on `localhost:3000`.

---

### 1. `POST /documents`

Uploads a document (`.pdf`, `.docx`, `.txt`, or `.md`) to be processed, chunked, and stored in the vector database.

```bash
# Uploads a file named "test.txt"
# The -F flag indicates a multipart/form-data request, which is used for file uploads.
# A session_id header is required to associate the document with a user session.
curl -X POST -F file=@example_document.txt -H "session_id: my-session-id" http://localhost:3000/documents
```

---

### 2. `GET /documents`

Retrieves a list of documents and their processing status for a given session.

```bash
# Retrieves documents for the session "my-session-id".
curl -X GET -H "session_id: my-session-id" http://localhost:3000/documents
```

---

### 3. `POST /documents/{doc_id}/quiz`

Triggers a job to generate a quiz from a processed document.

```bash
# Starts a quiz generation job for a document.
curl -X POST -H "Content-Type: application/json" -d '{
  "difficulty": "medium",
  "question_count": 5,
  "question_types": ["multiple-choice"],
  "topics": ["product features"]
}' http://localhost:3000/documents/YOUR_DOC_ID/quiz
```

---

### 4. `GET /quiz/{quiz_id}/status`

Checks the status of a quiz generation job.

```bash
# Checks the status of a quiz generation job.
curl -X GET http://localhost:3000/quiz/YOUR_QUIZ_ID/status
```

---

### 5. `POST /documents/{doc_id}/flashcards`

Triggers a job to generate flashcards from a processed document.

```bash
# Starts a flashcard generation job for a document.
curl -X POST -H "Content-Type: application/json" -d '{
  "count": 10
}' http://localhost:3000/documents/YOUR_DOC_ID/flashcards
```

---

### 6. `GET /flashcards/{flashcards_id}/status`

Checks the status of a flashcard generation job.

```bash
# Checks the status of a flashcard generation job.
curl -X GET http://localhost:3000/flashcards/YOUR_FLASHCARDS_ID/status
```

---

### 7. Gradio Web UI

A user-friendly web interface for interacting with the application is available by running the `app.py` script.

**Prerequisites:**

*   Ensure the backend server is running: `./devserver.sh`
*   Activate the virtual environment: `source .venv/bin/activate`

**Running the UI:**

In a **new terminal** (while the backend server is running in another), execute the following command:

```bash
python app.py
```

This will launch a Gradio interface, typically available at `http://127.0.0.1:7860`. The interface allows you to:

*   Upload documents.
*   Specify a topic or query.
*   Choose between generating a "Quiz" or "Flashcards".
*   View the generation status and results.
