
import logging
from sentence_transformers import CrossEncoder
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Load the cross-encoder model once when the module is imported.
# This is more efficient than loading it inside the function every time.
# "ms-marco-MiniLM-L-6-v2" is a lightweight but powerful model trained for semantic matching.
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_results(results: dict) -> dict:
    """
    Re-ranks retrieved results using a cross-encoder model.

    This function takes the initial list of retrieved documents and the original query,
    computes a more accurate relevance score for each document using a cross-encoder,
    and then re-sorts the documents based on this new score.

    Args:
        results (dict): A dictionary expected to contain:
                        - 'results': A list of document dictionaries.
                        - 'query': The original user query string.

    Returns:
        dict: The same dictionary with the 'results' list sorted by the new
              'rerank_score', and with new score fields attached to each document.
    """
    docs = results.get("results", [])
    query = results.get("query")

    if not docs or not query:
        logger.warning("No documents or query provided for reranking. Skipping.")
        return results

    logger.info(f"Reranking {len(docs)} documents for query: '{query}'")

    # Create pairs of [query, document_text] for the cross-encoder to score.
    pairs = [(query, doc["text"]) for doc in docs]

    # The predict method is highly optimized for batch processing.
    scores = cross_encoder.predict(pairs)
    logger.debug(f"Cross-encoder scores: {scores}")

    # Attach the new, more accurate scores to each document.
    for i, doc in enumerate(docs):
        doc["rerank_score"] = float(scores[i])

    # Sort the documents by the new rerank_score in descending order.
    docs.sort(key=lambda x: x["rerank_score"], reverse=True)

    # Optionally, normalize the scores to a 0-1 range for easier interpretation.
    max_score = np.max(scores) if len(scores) > 0 else 0.0
    min_score = np.min(scores) if len(scores) > 0 else 0.0

    for doc in docs:
        if max_score > min_score:
            doc["normalized_rerank_score"] = (doc["rerank_score"] - min_score) / (max_score - min_score)
        else:
            doc["normalized_rerank_score"] = 0.0
    
    reranked_docs = docs
    logger.info("Successfully reranked documents.")
    logger.debug(f"Reranked documents: {reranked_docs}")


    # Return the full results object with the reranked documents.
    return {
        **results,
        "results": reranked_docs
    }
