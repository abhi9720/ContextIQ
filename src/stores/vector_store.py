import os
import logging
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

# Configure logging
logger = logging.getLogger(__name__)

# The name of the model to use for embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# The directory to store the vector database
PERSIST_DIRECTORY = os.environ.get('PERSIST_DIRECTORY', 'db')

# Create the embedding function
embedding_function = SentenceTransformerEmbeddings(model_name=MODEL_NAME)

# Create the vector store
vector_store = Chroma(
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=embedding_function,
)

def embed_and_store(text, metadata, chunk_id):
    """Embeds the given text and stores it in the vector store with the provided metadata and ID."""
    logger.debug(f"Embedding and storing chunk with id: {chunk_id}")
    vector_store.add_texts(texts=[text], metadatas=[metadata], ids=[chunk_id])
    # Persist the vector store to disk
    vector_store.persist()
    logger.debug(f"Successfully persisted chunk with id: {chunk_id}")

def retrieve(query, k=5):
    """Retrieves the top k most similar documents to the given query."""
    logger.info(f"Retrieving top {k} documents for query: '{query}'")
    # Retrieve the most similar documents to the query
    results = vector_store.similarity_search_with_score(query, k=k)
    logger.debug(f"Raw retrieval results: {results}")

    # Format the results as a dictionary
    formatted_results = {
        'results': [
            {
                'text': doc.page_content,
                'metadata': doc.metadata,
                'score': score
            }
            for doc, score in results
        ]
    }
    logger.info(f"Retrieved {len(formatted_results['results'])} documents.")
    return formatted_results
