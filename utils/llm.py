import os
import google.generativeai as genai

def get_llm(node: str):
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.GenerativeModel("gemini-1.5-flash")
