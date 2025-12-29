
import gradio as gr
import requests
import time
import os
import uuid

API_URL = "http://127.0.0.1:3000"
SESSION_ID = str(uuid.uuid4())

def upload_file(files):
    if not files:
        return "No file uploaded.", None
    
    filepath = files[0].name
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = requests.post(
            f"{API_URL}/documents",
            files={"file": (filename, f)},
            headers={"session_id": SESSION_ID}
        )
    
    if response.status_code == 200:
        doc_id = response.json().get("doc_id")
        return f"Uploaded {filename}", doc_id
    else:
        return f"Error: {response.text}", None

def generate(doc_id, query, quiz_type):
    if not doc_id:
        return "Please upload a document first.", "", "", ""

    # Poll for document processing
    while True:
        status_response = requests.get(f"{API_URL}/documents", headers={"session_id": SESSION_ID})
        if status_response.status_code != 200:
            return "Error checking document status.", "", "", ""

        documents = status_response.json().get("documents", [])
        doc_info = next((doc for doc in documents if doc["doc_id"] == doc_id), None)
        
        if not doc_info:
            return "Document not found after upload.", "", "", ""
        
        if doc_info["status"] == "PROCESSED":
            break
        elif doc_info["status"] == "FAILED":
            return "Document processing failed.", "", "", ""
        
        yield f"Status: Document is {doc_info['status']}...", "", "", ""
        time.sleep(5)

    if quiz_type == "Quiz":
        request_body = {"difficulty": "medium", "question_count": 5, "question_types": ["multiple-choice"], "topics": [query]}
        create_response = requests.post(f"{API_URL}/documents/{doc_id}/quiz", json=request_body)
        if create_response.status_code != 200:
            return f"Error creating quiz: {create_response.text}", "", "", ""
        
        job_id = create_response.json().get("quiz_id")
        status_url = f"{API_URL}/quiz/{job_id}/status"
        
    elif quiz_type == "Flashcards":
        request_body = {"count": 10}
        create_response = requests.post(f"{API_URL}/documents/{doc_id}/flashcards", json=request_body)
        if create_response.status_code != 200:
            return f"Error creating flashcards: {create_response.text}", "", "", ""
            
        job_id = create_response.json().get("flashcards_id")
        status_url = f"{API_URL}/flashcards/{job_id}/status"
        
    else:
        return "Invalid quiz type.", "", "", ""

    if not job_id:
        return "Failed to get job ID.", "", "", ""

    # Poll for results
    while True:
        status_response = requests.get(status_url)
        if status_response.status_code != 200:
            return f"Error checking job status: {status_response.text}", "", "", ""
            
        status_data = status_response.json()
        status = status_data.get("status")
        
        if status == "READY":
            if quiz_type == "Quiz":
                return "Quiz generated!", status_data.get("questions"), "", job_id
            else:
                return "Flashcards generated!", "", status_data.get("flashcards"), job_id
        elif status == "FAILED":
            return "Generation failed.", "", "", job_id
            
        yield f"Status: {status}...", "", "", job_id
        time.sleep(5)

with gr.Blocks() as demo:
    doc_id_state = gr.State(None)
    job_id_state = gr.State(None)

    gr.Markdown("# Document-Based Quiz and Flashcard Generator")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 1. Upload Document")
            file_input = gr.File(file_count="single", file_types=[".pdf", ".docx"])
            upload_status = gr.Textbox(label="Upload Status", interactive=False)
            
            gr.Markdown("## 2. Configure Generation")
            query_input = gr.Textbox(label="Topic / Query")
            quiz_type_input = gr.Dropdown(["Quiz", "Flashcards"], label="Generation Type")
            generate_button = gr.Button("Generate")
            
            gr.Markdown("## 3. Generation Status")
            gen_status_output = gr.Textbox(label="Generation Status", interactive=False)

        with gr.Column(scale=2):
            gr.Markdown("## 4. Results")
            quiz_output = gr.JSON(label="Quiz Questions")
            flashcards_output = gr.JSON(label="Flashcards")

    file_input.upload(upload_file, inputs=[file_input], outputs=[upload_status, doc_id_state])
    
    generate_button.click(
        generate, 
        inputs=[doc_id_state, query_input, quiz_type_input], 
        outputs=[gen_status_output, quiz_output, flashcards_output, job_id_state]
    )

if __name__ == "__main__":
    demo.launch()
