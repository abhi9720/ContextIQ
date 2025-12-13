class MetadataStore:
    def __init__(self):
        self.documents = {}
        self.feedback = {}

    def add_document(self, doc_id, filename, file_path):
        self.documents[doc_id] = {"filename": filename, "file_path": file_path, "quality_score": 0}

    def add_feedback(self, doc_id, rating):
        if doc_id in self.documents:
            self.documents[doc_id]["quality_score"] += rating
            if doc_id not in self.feedback:
                self.feedback[doc_id] = []
            self.feedback[doc_id].append(rating)
