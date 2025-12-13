from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tempfile
import os

async def extract_and_chunk_file(file: UploadFile):
    """Extracts text from a file and chunks it."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        loader_map = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
        }

        ext = os.path.splitext(file.filename)[1]
        if ext not in loader_map:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        loader = loader_map[ext](tmp_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100, length_function=len)
        chunks = text_splitter.split_documents(documents)

        return [{"text": chunk.page_content, "paragraph_id": i, "start_offset": 0, "end_offset": len(chunk.page_content)} for i, chunk in enumerate(chunks)]

    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
