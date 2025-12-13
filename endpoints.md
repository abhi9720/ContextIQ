
### API Endpoints and `curl` Examples

Here are the `curl` commands to interact with the various endpoints of your RAG API.

**Note:** These commands assume the server is running on `localhost:3000`.

---

### 1. `POST /embed`

Uploads a document (`.pdf`, `.docx`, `.txt`, or `.md`) to be processed, chunked, and stored in the vector database.

```bash
# Uploads a file named "test.txt"
# The -F flag indicates a multipart/form-data request, which is used for file uploads.
curl -X POST -F file=@example_document.txt http://localhost:3000/embed
```

You can also include optional metadata with the upload:

```bash
# Uploads a file with an associated author.
curl -X POST -F "file=@example_document.txt" -F "metadata={"author":"John Doe"}" http://localhost:3000/embed
```

---

### 2. `POST /retrieve`

This is the main retrieval endpoint that not only fetches relevant chunks but also includes additional information like confidence scores and provenance. It is designed to be a more complete, production-ready retrieval endpoint.

```bash
# Retrieves the top 5 chunks for the query "product features".
# This uses a POST request, which is often better for longer or more complex queries.
curl -X POST -H "Content-Type: application/json" -d '{
  "query": "product features",
  "k": 5
}' http://localhost:3000/retrieve
```
