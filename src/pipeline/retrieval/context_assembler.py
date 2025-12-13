from typing import Dict, List

def assemble_context(results: Dict[str, List[Dict]]) -> List[str]:
    """
    Assembles a list of unique text chunks from the retrieved results.

    This function takes the results from the retrieval and reranking steps,
    extracts the text from each document, and removes any exact duplicates
    while preserving the order.

    Args:
        results: The dictionary of results, expected to contain a 'results' key
                 with a list of document dictionaries.

    Returns:
        A list of strings, where each string is a unique text chunk.
    """
    # Use dict.fromkeys to efficiently get unique texts while preserving order.
    unique_texts = list(dict.fromkeys([
        result['text'] for result in results.get('results', [])
    ]))
    return unique_texts
