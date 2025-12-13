
from dotenv import load_dotenv
load_dotenv() # Must be called before any other imports that need environment variables

import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uvicorn
from .pipeline.ingestion.file_processor import extract_and_chunk_file
from .stores.vector_store import embed_and_store, retrieve
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge
import time
from .stores.metadata_store import MetadataStore
import logging

# Import pipeline modules
from .pipeline.ingestion import validator as ingestion_validator
from .pipeline.ingestion import preprocessor as ingestion_preprocessor
from .pipeline.ingestion import metadata_generator as ingestion_metadata_generator
from .pipeline.ingestion import storage as ingestion_storage
from .pipeline.retrieval import query_validator as retrieval_query_validator
from .pipeline.retrieval import ranker as retrieval_ranker
from .pipeline.retrieval import prompt_manager as retrieval_prompt_manager
from .pipeline.retrieval import response_enhancer as retrieval_response_enhancer
from .pipeline.retrieval.context_assembler import assemble_context
from .pipeline.shared.optimizer import compress_context
from .pipeline.llm.context_enhancer import enhance_context
from .pipeline.llm.safety_filter import filter_safety
from .pipeline.llm.prompt_composer import compose_prompt
from .pipeline.llm.llm_invoker import invoke_llm

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
metadata_store = MetadataStore()

# Instrument the app with default metrics.
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app)

# Custom metrics
retrieval_latency_gauge = Gauge('retrieval_latency_ms', 'Retrieval latency in milliseconds')
avg_top_k_score_gauge = Gauge('avg_top_k_score', 'Average top-k score')

class RetrieveRequest(BaseModel):
    query: str
    k: int = Field(5, ge=1, le=100)

class RetrieveResponse(BaseModel):
    answer: str
    sources: List[Dict]

class FeedbackRequest(BaseModel):
    doc_id: str
    rating: int = Field(..., ge=-1, le=1, description="-1 for downvote, 1 for upvote")

@app.post("/embed")
async def embed(file: UploadFile = File(...), metadata: Optional[str] = Form(None)):
    """Orchestrates the document ingestion pipeline."""
    logger.info(f"Starting ingestion for file: {file.filename}")
    ingestion_validator.validate_file(file)
    logger.debug("File validation successful.")

    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, file.filename)
    
    await file.seek(0)
    ingestion_storage.save_raw_file(file, file_path)
    logger.debug(f"File saved to: {file_path}")
    await file.seek(0)

    chunks = await extract_and_chunk_file(file)
    doc_id = str(uuid.uuid4())
    metadata_store.add_document(doc_id, file.filename, file_path)
    logger.info(f"Generated doc_id: {doc_id} for file: {file.filename}")

    doc_level_metadata = {}
    if metadata:
        doc_level_metadata = json.loads(metadata)
    doc_level_metadata['source'] = file.filename
    doc_level_metadata['doc_id'] = doc_id
    logger.debug(f"Document level metadata: {doc_level_metadata}")

    chunk_ids = []
    for chunk in chunks:
        preprocessed_text = ingestion_preprocessor.preprocess_text(chunk['text'])
        generated_metadata = ingestion_metadata_generator.generate_metadata(preprocessed_text)

        chunk_id = f"{doc_id}_{chunk['paragraph_id']}"
        chunk_ids.append(chunk_id)
        
        chunk_metadata = doc_level_metadata.copy()
        chunk_metadata.update({
            "paragraph_id": chunk["paragraph_id"],
            "start_offset": chunk["start_offset"],
            "end_offset": chunk["end_offset"],
            "generated_metadata": json.dumps(generated_metadata)
        })
        
        embed_and_store(preprocessed_text, chunk_metadata, chunk_id)
        logger.debug(f"Embedded and stored chunk: {chunk_id}")
        
    logger.info(f"Successfully ingested file: {file.filename}, with {len(chunks)} chunks.")
    return {"filename": file.filename, "doc_id": doc_id, "num_chunks": len(chunks)}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve_v1(request: RetrieveRequest):
    """Orchestrates the retrieval and generation pipeline."""
    logger.info(f"Received retrieval request with query: '{request.query}' and k: {request.k}")
    safe_query = filter_safety(request.query, method='redact')
    retrieval_query_validator.validate_query(safe_query)
    logger.debug("Query validation successful.")

    start_time = time.time()
    retrieved_results = retrieve(safe_query, request.k)
    end_time = time.time()
    retrieval_latency = (end_time - start_time) * 1000
    retrieval_latency_gauge.set(retrieval_latency)
    logger.info(f"Retrieval latency: {retrieval_latency:.2f} ms")
    logger.debug(f"Retrieved results: {retrieved_results}")

    if retrieved_results and retrieved_results.get('results'):
        top_k_scores = [r.get('score', 0) for r in retrieved_results['results']]
        avg_top_k_score = sum(top_k_scores) / len(top_k_scores) if top_k_scores else 0
        avg_top_k_score_gauge.set(avg_top_k_score)
        logger.debug(f"Average top-k score: {avg_top_k_score}")

    # Add the query to the results object for the reranker to use.
    retrieved_results["query"] = safe_query
    reranked_results = retrieval_ranker.rerank_results(retrieved_results)
    logger.debug(f"Reranked results: {reranked_results}")

    context_chunks = assemble_context(reranked_results)
    compressed_chunks = compress_context(context_chunks, safe_query)
    context = "\n\n---\n\n".join(compressed_chunks)
    logger.debug(f"Assembled and compressed context: {context}")
    
    metadata = [result['metadata'] for result in reranked_results.get('results', [])]
    enhanced_context = enhance_context(context, metadata)
    logger.debug(f"Enhanced context: {enhanced_context}")
    
    prompt = compose_prompt(enhanced_context, safe_query)
    logger.debug(f"Composed prompt: {prompt}")

    answer = invoke_llm(prompt)
    logger.info("LLM invoked.")
    logger.debug(f"LLM response: {answer}")

    sources = [
        {"source": result['metadata'].get('source'), "doc_id": result['metadata'].get('doc_id')}
        for result in reranked_results.get('results', [])
    ]
    unique_sources = [dict(t) for t in {tuple(d.items()) for d in sources}]
    logger.debug(f"Sources: {unique_sources}")

    enhanced_response = retrieval_response_enhancer.enhance_response(answer, unique_sources)
    logger.info("Response enhanced.")
    return enhanced_response


@app.post("/api/v1/feedback")
def feedback_v1(request: FeedbackRequest):
    """
    Receives user feedback and updates the document's quality score.
    """
    logger.info(f"Received feedback for doc_id: {request.doc_id}, rating: {request.rating}")
    metadata_store.add_feedback(request.doc_id, request.rating)
    return {"status": "success", "doc_id": request.doc_id, "rating": request.rating}


if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
