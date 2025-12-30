import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:3000';

function App() {
    const [documents, setDocuments] = useState([]);
    const [uploadStatus, setUploadStatus] = useState('');
    const [chatQuery, setChatQuery] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [generationStatus, setGenerationStatus] = useState('');
    const [generatedContent, setGeneratedContent] = useState(null);
    const [sessionId] = useState(Math.random().toString(36).substring(7));
    const fileInputRef = useRef(null);

    // Poll for document status changes
    useEffect(() => {
        const pollInterval = setInterval(async () => {
            if (sessionId) {
                try {
                    const response = await axios.get(`${API_URL}/documents`, { headers: { 'session_id': sessionId } });
                    setDocuments(response.data.documents);
                } catch (error) {
                    console.error('Error polling for documents:', error);
                }
            }
        }, 5000); // Poll every 5 seconds

        return () => clearInterval(pollInterval);
    }, [sessionId]);


    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        if (selectedFile) {
            handleUpload(selectedFile);
        }
    };

    const handleUpload = async (fileToUpload) => {
        if (!fileToUpload) return;

        const formData = new FormData();
        formData.append('file', fileToUpload);

        try {
            setUploadStatus('Uploading...');
            const response = await axios.post(`${API_URL}/documents`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'session_id': sessionId,
                },
            });
            setUploadStatus(`File uploaded successfully. Processing...`);
            // Manually add the new document to the list for immediate feedback
            setDocuments(prevDocs => [...prevDocs, { doc_id: response.data.doc_id, filename: fileToUpload.name, status: 'UPLOADED', quality_score: 0 }]);
        } catch (error) {
            setUploadStatus('File upload failed.');
            console.error('Error uploading file:', error);
        }
    };

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!chatQuery.trim()) return;
        // Placeholder for chat functionality
        setChatHistory([...chatHistory, { type: 'user', message: chatQuery }]);
        setChatQuery('');
    };
    
    const handleGeneration = async (type) => {
        const latestDocuments = documents;
        const processedDocs = latestDocuments.filter(d => d.status === 'PROCESSED');

        if (processedDocs.length === 0) {
            setGenerationStatus('No documents are processed and ready for use.');
            return;
        }
        // For simplicity, using the most recently uploaded processed document
        const docToUse = processedDocs[processedDocs.length - 1];

        setGenerationStatus(`Generating ${type}...`);
        setGeneratedContent(null);

        const endpoint = type === 'quiz' ? 'quiz' : 'flashcards';
        const requestBody = type === 'quiz'
            ? { difficulty: 'medium', question_count: 5, question_types: ['multiple-choice'], topics: [] }
            : { count: 10 };

        try {
            const createResponse = await axios.post(`${API_URL}/documents/${docToUse.doc_id}/${endpoint}`, requestBody);
            const jobId = type === 'quiz' ? createResponse.data.quiz_id : createResponse.data.flashcards_id;

            const pollGeneration = setInterval(async () => {
                try {
                    const statusResponse = await axios.get(`${API_URL}/${endpoint}/${jobId}/status`);
                    const { status, questions, flashcards } = statusResponse.data;

                    if (status === 'READY') {
                        setGeneratedContent(type === 'quiz' ? questions : flashcards);
                        setGenerationStatus(`${type.charAt(0).toUpperCase() + type.slice(1)} generated successfully.`);
                        clearInterval(pollGeneration);
                    } else if (status === 'FAILED') {
                        setGenerationStatus(`Failed to generate ${type}.`);
                        clearInterval(pollGeneration);
                    } else {
                        setGenerationStatus(`Generation in progress... Status: ${status}`);
                    }
                } catch (pollError) {
                    console.error(`Error polling for ${type} status:`, pollError);
                    setGenerationStatus(`Error checking ${type} status.`);
                    clearInterval(pollGeneration);
                }
            }, 5000);
        } catch (error) {
            console.error(`Error starting ${type} generation:`, error);
            setGenerationStatus(`Failed to start ${type} generation.`);
        }
    };

    return (
        <div className="app-container">
            {/* Left Panel: Asset Library */}
            <div className="left-panel">
                <h2 className="panel-header">Asset Library</h2>
                <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    style={{ display: 'none' }} 
                    accept=".pdf,.docx,.txt"
                />
                <button className="import-button" onClick={() => fileInputRef.current.click()}>
                    + Import Source
                </button>
                {uploadStatus && <p>{uploadStatus}</p>}
                <div className="document-list">
                    <ul>
                        {documents.map(doc => (
                            <li key={doc.doc_id}>
                                {doc.filename}
                                <span className="status">({doc.status})</span>
                            </li>
                        ))}
                    </ul>
                    {documents.length === 0 && <p>No documents found.</p>}
                </div>
            </div>

            {/* Middle Panel: Research Engine */}
            <div className="middle-panel">
                 <h2 className="panel-header">Research Engine</h2>
                <div className="chat-window">
                    <div className="chat-messages">
                        {chatHistory.map((msg, index) => (
                            <div key={index} className={`chat-message ${msg.type}`}>
                                {msg.message}
                            </div>
                        ))}
                         {chatHistory.length === 0 && <p>Summarize the key themes across these documents.</p>}
                    </div>
                    <form onSubmit={handleChatSubmit} className="chat-input-container">
                        <input
                            type="text"
                            className="chat-input"
                            value={chatQuery}
                            onChange={(e) => setChatQuery(e.target.value)}
                            placeholder="Inquire across documents..."
                        />
                    </form>
                </div>
            </div>

            {/* Right Panel: Asset Studio */}
            <div className="right-panel">
                <h2 className="panel-header">Asset Studio</h2>
                <h3>Knowledge Utilities</h3>
                <div className="utility-card" onClick={() => handleGeneration('quiz')}>
                    <h3>Deep Quiz</h3>
                    <p>Active recall testing</p>
                </div>
                <div className="utility-card" onClick={() => handleGeneration('flashcards')}>
                    <h3>Flashcards</h3>
                    <p>Key concept mastery</p>
                </div>
                
                <h3 style={{ marginTop: '20px' }}>Knowledge Vault</h3>
                <div className="knowledge-vault">
                    {generationStatus && <p>{generationStatus}</p>}
                    {generatedContent && (
                        <pre className="json-output">
                            {JSON.stringify(generatedContent, null, 2)}
                        </pre>
                    )}
                    {!generatedContent && !generationStatus && <p>Studio Empty</p>}
                </div>
            </div>
        </div>
    );
}

export default App;
