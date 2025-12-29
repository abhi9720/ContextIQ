
from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import json
import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

from .stores.metadata_store import MetadataStore
from .stores.vector_store import embed_and_store, retrieve
from .pipeline.ingestion.file_processor import extract_and_chunk_file
from .pipeline.ingestion import storage as ingestion_storage
from .pipeline.ingestion import validator as ingestion_validator
from .pipeline.llm.prompt_composer import compose_prompt
from .pipeline.llm.llm_invoker import invoke_llm
from .pipeline.retrieval.context_assembler import assemble_context

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
metadata_store = MetadataStore()

# Background executor for processing-intensive tasks
executor = ThreadPoolExecutor(max_workers=os.cpu_count())
loop = asyncio.get_event_loop()

# --- Request/Response Models ---

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    status: str
    quality_score: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]

class DocumentUploadResponse(BaseModel):
    doc_id: str
    status: str

class QuizRequest(BaseModel):
    difficulty: str = Field("medium", description="Difficulty of the quiz")
    question_count: int = Field(5, ge=1, le=20, description="Number of questions")
    question_types: List[str] = Field(["multiple-choice"], description="Types of questions")
    topics: Optional[List[str]] = Field(None, description="Optional topics to focus on")

class QuizCreateResponse(BaseModel):
    quiz_id: str
    status: str

class QuizStatusResponse(BaseModel):
    quiz_id: str
    status: str
    questions: Optional[List[Dict]] = None

class FlashcardRequest(BaseModel):
    count: int = Field(10, ge=1, le=50, description="Number of flashcards")

class FlashcardCreateResponse(BaseModel):
    flashcards_id: str
    status: str

class FlashcardStatusResponse(BaseModel):
    flashcards_id: str
    status: str
    flashcards: Optional[List[Dict]] = None

# --- Background Processing Functions ---

def process_document_background(doc_id: str):
    """Background task to process a single document."""
    try:
        doc_info = metadata_store.get_document(doc_id)
        if not doc_info:
            logger.error(f"[Worker] Document {doc_id} not found.")
            return

        logger.info(f"[Worker] Starting processing for document: {doc_id}")
        metadata_store.update_document_status(doc_id, "PROCESSING")

        # 1. Extract and chunk file
        with open(doc_info['file_path'], 'rb') as f:
            temp_upload_file = UploadFile(filename=doc_info['filename'], file=f)
            chunks = asyncio.run(extract_and_chunk_file(temp_upload_file))

        if not chunks:
            metadata_store.update_document_status(doc_id, "FAILED")
            logger.error(f"[Worker] Failed to extract chunks from {doc_id}.")
            return

        # 2. Store chunks and generate embeddings
        for chunk in chunks:
            chunk_id = f"{doc_id}_{chunk['paragraph_id']}"
            chunk_metadata = {
                "doc_id": doc_id,
                "source": doc_info['filename'],
                "paragraph_id": chunk["paragraph_id"],
            }
            embed_and_store(chunk['text'], chunk_metadata, chunk_id)

        metadata_store.add_chunks(doc_id, chunks)
        metadata_store.update_document_status(doc_id, "PROCESSED")
        logger.info(f"[Worker] Successfully processed document: {doc_id}")

    except Exception as e:
        metadata_store.update_document_status(doc_id, "FAILED")
        logger.error(f"[Worker] Error processing document {doc_id}: {e}", exc_info=True)

def generate_quiz_background(quiz_id: str):
    """Background task to generate a quiz."""
    logger.debug(f"[QuizWorker] Starting quiz generation for quiz_id: {quiz_id}")
    try:
        quiz_info = metadata_store.get_quiz(quiz_id)
        if not quiz_info:
            logger.error(f"[QuizWorker] Quiz {quiz_id} not found.")
            return
        
        logger.debug(f"[QuizWorker] Quiz info retrieved: {quiz_info}")
        doc_id = quiz_info['doc_id']
        logger.info(f"[QuizWorker] Starting quiz generation for quiz_id: {quiz_id} on doc: {doc_id}")

        logger.debug("[QuizWorker] Retrieving context from vector store...")
        retrieved_results = retrieve(query="", k=10, filter={"doc_id": doc_id})
        logger.debug(f"[QuizWorker] Retrieved results: {retrieved_results}")

        if not retrieved_results.get('results'):
            logger.error("[QuizWorker] No results retrieved from vector store. Aborting.")
            metadata_store.update_quiz_status(quiz_id, "FAILED")
            return
            
        logger.debug("[QuizWorker] Assembling context...")
        context_chunks = assemble_context(retrieved_results)
        context = "\n\n---\n\n".join(context_chunks)
        logger.debug(f"[QuizWorker] Assembled context: {context}")

        logger.debug("[QuizWorker] Composing prompt...")
        prompt = compose_prompt(
            context,
            f"Generate a {quiz_info['request_params']['difficulty']} quiz with {quiz_info['request_params']['question_count']} questions in JSON format."
        )
        logger.debug(f"[QuizWorker] Composed prompt: {prompt}")

        logger.debug("[QuizWorker] Invoking LLM...")
        llm_response_str = invoke_llm(prompt)
        logger.debug(f"[QuizWorker] LLM response: {llm_response_str}")
        
        try:
            logger.debug("[QuizWorker] Cleaning and parsing LLM response...")
            if llm_response_str.startswith("```json"):
                llm_response_str = llm_response_str[7:]
            if llm_response_str.endswith("```"):
                llm_response_str = llm_response_str[:-3]
            
            data = json.loads(llm_response_str)

            questions = None
            if isinstance(data, list):
                questions = data
            elif isinstance(data, dict):
                questions = data.get("quiz")

            if not isinstance(questions, list):
                logger.error("[QuizWorker] 'quiz' key not found or is not a list in LLM response.")
                raise ValueError("'quiz' key not found or is not a list.")

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[QuizWorker] Failed to parse or validate LLM response: {e}")
            metadata_store.update_quiz_status(quiz_id, "FAILED")
            return

        logger.debug("[QuizWorker] Updating quiz status to READY...")
        metadata_store.update_quiz_status(quiz_id, "READY", questions=questions)
        logger.info(f"[QuizWorker] Successfully generated quiz: {quiz_id}")

    except Exception as e:
        logger.error(f"[QuizWorker] An unexpected error occurred: {e}", exc_info=True)
        metadata_store.update_quiz_status(quiz_id, "FAILED")
        logger.error(f"[QuizWorker] Error generating quiz {quiz_id}: {e}", exc_info=True)

def generate_flashcards_background(flashcards_id: str):
    """Background task to generate flashcards."""
    logger.debug(f"[FlashcardWorker] Starting flashcard generation for flashcards_id: {flashcards_id}")
    try:
        flashcards_info = metadata_store.get_flashcards(flashcards_id)
        if not flashcards_info:
            logger.error(f"[FlashcardWorker] Flashcards {flashcards_id} not found.")
            return
        
        logger.debug(f"[FlashcardWorker] Flashcards info retrieved: {flashcards_info}")
        doc_id = flashcards_info['doc_id']
        logger.info(f"[FlashcardWorker] Starting flashcard generation for flashcards_id: {flashcards_id} on doc: {doc_id}")

        logger.debug("[FlashcardWorker] Retrieving context from vector store...")
        retrieved_results = retrieve(query="", k=10, filter={"doc_id": doc_id})
        logger.debug(f"[FlashcardWorker] Retrieved results: {retrieved_results}")

        if not retrieved_results.get('results'):
            logger.error("[FlashcardWorker] No results retrieved from vector store. Aborting.")
            metadata_store.update_flashcards_status(flashcards_id, "FAILED")
            return
            
        logger.debug("[FlashcardWorker] Assembling context...")
        context_chunks = assemble_context(retrieved_results)
        context = "\n\n---\n\n".join(context_chunks)
        logger.debug(f"[FlashcardWorker] Assembled context: {context}")

        logger.debug("[FlashcardWorker] Composing prompt...")
        prompt = compose_prompt(
            context,
            f"Generate {flashcards_info['request_params']['count']} flashcards in JSON format. Each flashcard should have a 'front' and a 'back'."
        )
        logger.debug(f"[FlashcardWorker] Composed prompt: {prompt}")

        logger.debug("[FlashcardWorker] Invoking LLM...")
        llm_response_str = invoke_llm(prompt)
        logger.debug(f"[FlashcardWorker] LLM response: {llm_response_str}")
        
        try:
            logger.debug("[FlashcardWorker] Cleaning and parsing LLM response...")
            # Clean the response string
            if llm_response_str.startswith("```json"):
                llm_response_str = llm_response_str[7:]
            if llm_response_str.endswith("```"):
                llm_response_str = llm_response_str[:-3]
            
            data = json.loads(llm_response_str)

            flashcards = None
            if isinstance(data, list):
                flashcards = data
            elif isinstance(data, dict):
                flashcards = data.get("flashcards")

            if not isinstance(flashcards, list):
                logger.error("[FlashcardWorker] 'flashcards' key not found or is not a list in LLM response.")
                raise ValueError("'flashcards' key not found or is not a list.")

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[FlashcardWorker] Failed to parse or validate LLM response: {e}")
            metadata_store.update_flashcards_status(flashcards_id, "FAILED")
            return

        logger.debug("[FlashcardWorker] Updating flashcards status to READY...")
        metadata_store.update_flashcards_status(flashcards_id, "READY", flashcards=flashcards)
        logger.info(f"[FlashcardWorker] Successfully generated flashcards: {flashcards_id}")

    except Exception as e:
        logger.error(f"[FlashcardWorker] An unexpected error occurred: {e}", exc_info=True)
        metadata_store.update_flashcards_status(flashcards_id, "FAILED")
        logger.error(f"[FlashcardWorker] Error generating flashcards {flashcards_id}: {e}", exc_info=True)


async def poll_for_uploaded_documents():
    """Periodically polls the metadata store for documents with 'UPLOADED' status."""
    while True:
        try:
            uploaded_docs = metadata_store.get_documents_by_status('UPLOADED')
            if uploaded_docs:
                logger.info(f"[PollingWorker] Found {len(uploaded_docs)} documents to process.")
                for doc in uploaded_docs:
                    # Use the executor to run the synchronous processing function in a separate thread
                    loop.run_in_executor(executor, process_document_background, doc['doc_id'])
        except Exception as e:
            logger.error(f"[PollingWorker] Error polling for documents: {e}", exc_info=True)
        await asyncio.sleep(10) # Poll every 10 seconds

@app.on_event("startup")
async def startup_event():
    """On application startup, starts the background polling worker."""
    logger.info("Application starting up. Initializing background worker.")
    asyncio.create_task(poll_for_uploaded_documents())

# --- API Endpoints ---

@app.get("/documents", response_model=DocumentListResponse)
def get_documents(
    session_id: Optional[str] = Header(None)
):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id header is required.")
    
    user_docs = metadata_store.get_documents_by_session(session_id)
    
    return {"documents": [
        DocumentMetadata(
            doc_id=doc['doc_id'], 
            filename=doc['filename'], 
            status=doc['status'],
            quality_score=doc['quality_score']
        ) for doc in user_docs
    ]}

@app.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...), 
    session_id: Optional[str] = Header(None)
):
    ingestion_validator.validate_file(file)
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{doc_id}_{file.filename}")
    
    await file.seek(0)
    ingestion_storage.save_raw_file(file, file_path)
    
    metadata_store.add_document(doc_id, file.filename, file_path, session_id)
    
    logger.info(f"Document {doc_id} uploaded. Worker will pick it up for processing.")
    return {"doc_id": doc_id, "status": "UPLOADED"}

@app.post("/documents/{doc_id}/quiz", response_model=QuizCreateResponse)
def create_quiz_job(
    doc_id: str,
    request: QuizRequest,
    background_tasks: BackgroundTasks,
):
    doc_info = metadata_store.get_document(doc_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    if doc_info['status'] != "PROCESSED":
        raise HTTPException(status_code=400, detail=f"Document status is '{doc_info['status']}', not 'PROCESSED'.")

    request_hash = hashlib.sha256(json.dumps(request.dict(), sort_keys=True).encode()).hexdigest()
    quiz_id = f"quiz_{doc_id}_{request_hash}"

    existing_quiz = metadata_store.get_quiz(quiz_id)
    if existing_quiz:
        return {"quiz_id": quiz_id, "status": existing_quiz['status']}

    metadata_store.create_quiz(quiz_id, doc_id, request.dict())
    background_tasks.add_task(generate_quiz_background, quiz_id)
    
    return {"quiz_id": quiz_id, "status": "GENERATING"}

@app.get("/quiz/{quiz_id}/status", response_model=QuizStatusResponse)
def get_quiz_status(quiz_id: str):
    quiz_info = metadata_store.get_quiz(quiz_id)
    if not quiz_info:
        raise HTTPException(status_code=404, detail="Quiz not found.")
        
    return {
        "quiz_id": quiz_id,
        "status": quiz_info['status'],
        "questions": quiz_info.get('questions') if quiz_info['status'] == "READY" else None
    }

@app.post("/documents/{doc_id}/flashcards", response_model=FlashcardCreateResponse)
def create_flashcards_job(
    doc_id: str,
    request: FlashcardRequest,
    background_tasks: BackgroundTasks,
):
    doc_info = metadata_store.get_document(doc_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    if doc_info['status'] != "PROCESSED":
        raise HTTPException(status_code=400, detail=f"Document status is '{doc_info['status']}', not 'PROCESSED'.")

    request_hash = hashlib.sha256(json.dumps(request.dict(), sort_keys=True).encode()).hexdigest()
    flashcards_id = f"flashcards_{doc_id}_{request_hash}"

    existing_flashcards = metadata_store.get_flashcards(flashcards_id)
    if existing_flashcards:
        return {"flashcards_id": flashcards_id, "status": existing_flashcards['status']}

    metadata_store.create_flashcards(flashcards_id, doc_id, request.dict())
    background_tasks.add_task(generate_flashcards_background, flashcards_id)
    
    return {"flashcards_id": flashcards_id, "status": "GENERATING"}

@app.get("/flashcards/{flashcards_id}/status", response_model=FlashcardStatusResponse)
def get_flashcards_status(flashcards_id: str):
    flashcards_info = metadata_store.get_flashcards(flashcards_id)
    if not flashcards_info:
        raise HTTPException(status_code=404, detail="Flashcards not found.")
        
    return {
        "flashcards_id": flashcards_id,
        "status": flashcards_info['status'],
        "flashcards": flashcards_info.get('flashcards') if flashcards_info['status'] == "READY" else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
