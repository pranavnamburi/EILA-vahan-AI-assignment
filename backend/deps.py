import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def init_genai():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    return genai

def get_genai_llm(model_name="gemini-2.0-flash-lite"):
    """Return a LangChain-compatible Gemini model"""
    api_key = os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)