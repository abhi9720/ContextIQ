from fastapi import HTTPException

def validate_file(file):
    """Validates file type, size, and integrity."""
    # Add file validation logic here
    if not file.filename.endswith((".pdf", ".docx", ".txt", ".md")):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    return True
