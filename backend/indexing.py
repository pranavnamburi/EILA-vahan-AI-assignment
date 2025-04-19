import os
from typing import List, Dict
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

# Embeddings instance
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# Directory for storing FAISS indexes
INDEX_DIR = os.path.join(os.path.dirname(__file__), "../indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

def create_session_index_path(session_id: str) -> str:
    """Create a unique path for the session's FAISS index."""
    return os.path.join(INDEX_DIR, session_id)

async def index_documents(session_id: str, documents: List[Dict]) -> str:
    """
    Process and index the documents from research.
    Returns the path to the created FAISS index.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )
    
    # Convert to LangChain Document format with source and type metadata
    docs = []
    for doc in documents:
        chunks = text_splitter.create_documents(
            texts=[doc["text"]],
            metadatas=[{
                "source": doc["source"], 
                "type": doc.get("type", "unknown")
            }]
        )
        docs.extend(chunks)
    
    # Create vector store
    index_path = create_session_index_path(session_id)
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(index_path)
    
    return index_path

def get_session_index(session_id: str) -> FAISS:
    """Retrieve the FAISS index for a session."""
    index_path = create_session_index_path(session_id)
    if os.path.exists(index_path):
        return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    return None