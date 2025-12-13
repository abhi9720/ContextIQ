
import os
from typing import List
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

def compress_context(context: List[str], query: str) -> List[str]:
    """
    Compresses context using Gemini via LangChain based on the query.
    Each chunk is reduced to its essential information in relation to the query.
    """
    # Convert each text chunk to a LangChain Document object
    docs = [Document(page_content=chunk) for chunk in context if chunk.strip()]

    # Initialize Gemini model with API key
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    # Create a chain extractor
    compressor = LLMChainExtractor.from_llm(llm)

    # Perform compression using the query
    compressed_docs = compressor.compress_documents(docs, query)

    # Return list of reduced text chunks
    return [doc.page_content.strip() for doc in compressed_docs if doc.page_content.strip()]
