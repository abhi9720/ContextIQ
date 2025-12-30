
import logging
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class MetadataStore:
    """A simple in-memory metadata store to track documents, chunks, quizzes, and flashcards."""
    def __init__(self):
        self.documents: Dict[str, Dict] = {}
        self.chunks: Dict[str, List[Dict]] = {}  # doc_id -> list of chunks
        self.quizzes: Dict[str, Dict] = {}
        self.flashcards: Dict[str, Dict] = {}
        self.feedback: Dict[str, List] = {}

    def add_document(self, doc_id: str, filename: str, file_path: str, session_id: Optional[str] = None) -> Dict:
        """Adds a document to the store with an initial 'UPLOADED' status."""
        if doc_id in self.documents:
            logger.warning(f"Document with id {doc_id} already exists. Overwriting.")
        
        doc_metadata = {
            'doc_id': doc_id,
            'filename': filename,
            'file_path': file_path,
            'session_id': session_id,
            'status': 'UPLOADED',  # Initial status
            'quality_score': 0
        }
        self.documents[doc_id] = doc_metadata
        logger.info(f"Added document: {doc_id} with status 'UPLOADED'")
        return doc_metadata

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieves a document from the store."""
        return self.documents.get(doc_id)

    def get_documents_by_status(self, status: str) -> List[Dict]:
        """Retrieves all documents with a specific status."""
        return [doc for doc in self.documents.values() if doc.get('status') == status]

    def update_document_status(self, doc_id: str, status: str):
        """Updates the status of a document."""
        if doc_id in self.documents:
            self.documents[doc_id]['status'] = status
            logger.info(f"Updated status for doc_id: {doc_id} to '{status}'")
        else:
            logger.warning(f"Document with doc_id: {doc_id} not found for status update.")
            
    def get_documents_by_session(self, session_id: str) -> List[Dict]:
        """Retrieves all documents for a given session."""
        return [doc for doc in self.documents.values() if doc.get('session_id') == session_id]

    def add_chunks(self, doc_id: str, chunks: List[Dict]):
        """Adds processed chunks for a document."""
        self.chunks[doc_id] = chunks
        logger.info(f"Added {len(chunks)} chunks for doc_id: {doc_id}")

    def get_chunks(self, doc_id: str) -> Optional[List[Dict]]:
        """Retrieves all chunks for a document."""
        return self.chunks.get(doc_id)

    def add_feedback(self, doc_id: str, rating: int):
        """Adds feedback for a document and updates its quality score."""
        if doc_id in self.documents:
            self.documents[doc_id]['quality_score'] += rating
            if doc_id not in self.feedback:
                self.feedback[doc_id] = []
            self.feedback[doc_id].append(rating)
            logger.info(f"Updated quality score for doc_id: {doc_id} to {self.documents[doc_id]['quality_score']}")
        else:
            logger.warning(f"Document with doc_id: {doc_id} not found for feedback.")

    def create_quiz(self, quiz_id: str, doc_id: str, request_params: Dict) -> Dict:
        """Creates a new quiz record with 'GENERATING' status."""
        quiz_metadata = {
            "quiz_id": quiz_id,
            "doc_id": doc_id,
            "status": "GENERATING",
            "request_params": request_params,
            "questions": []
        }
        self.quizzes[quiz_id] = quiz_metadata
        logger.info(f"Created quiz {quiz_id} for doc_id {doc_id} with status 'GENERATING'")
        return quiz_metadata
        
    def get_quiz(self, quiz_id: str) -> Optional[Dict]:
        """Retrieves a quiz from the store."""
        return self.quizzes.get(quiz_id)

    def update_quiz_status(self, quiz_id: str, status: str, questions: Optional[List[Dict]] = None):
        """Updates the status and content of a quiz."""
        if quiz_id in self.quizzes:
            self.quizzes[quiz_id]['status'] = status
            if questions:
                self.quizzes[quiz_id]['questions'] = questions
            logger.info(f"Updated status for quiz_id: {quiz_id} to '{status}'")
        else:
            logger.warning(f"Quiz with quiz_id: {quiz_id} not found for status update.")

    def create_flashcards(self, flashcards_id: str, doc_id: str, request_params: Dict) -> Dict:
        """Creates a new flashcard set with 'GENERATING' status."""
        flashcards_metadata = {
            "flashcards_id": flashcards_id,
            "doc_id": doc_id,
            "status": "GENERATING",
            "request_params": request_params,
            "flashcards": []
        }
        self.flashcards[flashcards_id] = flashcards_metadata
        logger.info(f"Created flashcards {flashcards_id} for doc_id {doc_id} with status 'GENERATING'")
        return flashcards_metadata

    def get_flashcards(self, flashcards_id: str) -> Optional[Dict]:
        """Retrieves a flashcard set from the store."""
        return self.flashcards.get(flashcards_id)

    def update_flashcards_status(self, flashcards_id: str, status: str, flashcards: Optional[List[Dict]] = None):
        """Updates the status and content of a flashcard set."""
        if flashcards_id in self.flashcards:
            self.flashcards[flashcards_id]['status'] = status
            if flashcards:
                self.flashcards[flashcards_id]['flashcards'] = flashcards
            logger.info(f"Updated status for flashcards_id: {flashcards_id} to '{status}'")
        else:
            logger.warning(f"Flashcards with flashcards_id: {flashcards_id} not found for status update.")
