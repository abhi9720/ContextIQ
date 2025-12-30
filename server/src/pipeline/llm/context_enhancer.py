
from typing import List, Dict

def enhance_context(context: str, metadata: List[Dict]) -> str:
    """
    Enhances the context by prepending a summary of the source documents.

    Args:
        context: The main block of text retrieved from the vector store.
        metadata: A list of metadata dictionaries for each retrieved chunk.

    Returns:
        The enhanced context string.
    """
    if not metadata:
        return context

    # Extract unique source filenames from the metadata
    sources = list(set(meta.get('source') for meta in metadata if meta.get('source')))
    
    if not sources:
        return context

    source_summary = "The following information is derived from these documents: " + ", ".join(sources) + ".\n\n"
    
    enhanced_context = source_summary + context
    return enhanced_context
