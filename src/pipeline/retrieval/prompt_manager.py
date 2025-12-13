def get_prompt_template(task):
    """Returns a prompt template for a given task."""
    templates = {
        "qa": "Answer the following question based on the context provided:\n\nContext:\n{context}\n\nQuestion:\n{question}",
        "summary": "Summarize the following text:\n\n{context}"
    }
    return templates.get(task, templates["qa"]) # Default to QA
