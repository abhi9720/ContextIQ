
import google.generativeai as genai
import os

def invoke_llm(prompt):
    """Invokes the LLM to generate a response."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text
