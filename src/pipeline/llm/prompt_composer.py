

def compose_prompt(context: str, query: str) -> str:
    """
    Composes the final prompt to be sent to the LLM, combining a system
    message, the retrieved context, and the user's query.

    Args:
        context: The relevant text retrieved from the knowledge base.
        query: The user's original question.

    Returns:
        The fully formatted prompt string.
    """
    system_message = (
        "Use the following pieces of context to answer the user's question. "
        "This is a private knowledge base. Do not use any external information. "
        "If you don't know the answer from the context provided, just say that you don't know, "
        "don't try to make up an answer."
    )

    prompt = f"""{system_message}

    CONTEXT:
    ---
    {context}
    ---

    QUESTION:
    {query}

ANSWER:"""
    
    return prompt
