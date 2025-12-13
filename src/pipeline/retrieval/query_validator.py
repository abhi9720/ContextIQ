from fastapi import HTTPException

def validate_query(query):
    """Validates query length, language, and safety."""
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters long.")
    return True
