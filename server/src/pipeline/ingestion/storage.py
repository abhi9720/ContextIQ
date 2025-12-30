import os
import shutil

def save_raw_file(file, file_path):
    """Saves the raw file to the specified path."""
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
