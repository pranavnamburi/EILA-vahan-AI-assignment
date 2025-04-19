from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid

from backend.deps import init_genai
from backend.research import perform_research
from backend.qa import get_clarification_questions, analyze_preferences
from backend.report import generate_report, modify_report
from backend.indexing import index_documents

# Define request/response models
class SessionRequest(BaseModel):
    topic: Optional[str] = None

class ResearchRequest(BaseModel):
    topic: str
    objectives: List[str]

class ClarifyRequest(BaseModel):
    answers: Dict

class ReportRequest(BaseModel):
    session_id: str
    preferences: Dict

class FeedbackRequest(BaseModel):
    session_id: str
    feedback: Dict

# Initialize FastAPI
app = FastAPI()

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
genai = init_genai()

# In-memory session storage (for demo purposes)
# In production, use a database
sessions = {}

@app.post("/start_session")
async def start_session(request: SessionRequest = None):
    """Initialize a new learning session"""
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    sessions[session_id] = {
        "id": session_id,
        "topic": request.topic if request else None,
        "documents": [],
        "index_path": None,
        "preferences": {}
    }
    return {"session_id": session_id}

@app.post("/research")
async def research_endpoint(payload: ResearchRequest):
    """Perform research on the given topic"""
    if not payload.topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    
    # Start a new session if topic is provided
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    sessions[session_id] = {"id": session_id, "topic": payload.topic}
    
    # Perform research
    docs = await perform_research(payload.topic, payload.objectives)
    
    # Store documents in session
    sessions[session_id]["documents"] = docs
    sessions[session_id]["objectives"] = payload.objectives
    
    # Index the documents
    index_path = await index_documents(session_id, docs)
    sessions[session_id]["index_path"] = index_path
    
    return {
        "session_id": session_id,
        "documents": docs,
        "summary": f"Found {len(docs)} relevant sources on {payload.topic}"
    }

@app.post("/clarify")
async def clarify_endpoint(payload: ClarifyRequest):
    """Get clarification questions based on answers so far"""
    if not payload.answers:
        raise HTTPException(status_code=400, detail="Answers object is required")
    
    questions = get_clarification_questions(payload.answers)
    
    # If a session_id is provided, update the session with answers
    session_id = payload.answers.get("session_id")
    if session_id and session_id in sessions:
        sessions[session_id]["answers"] = payload.answers
    
    return {"questions": questions}

@app.post("/analyze_preferences")
async def analyze_preferences_endpoint(payload: Dict):
    """Analyze user preferences to customize the report"""
    if "answers" not in payload:
        raise HTTPException(status_code=400, detail="Answers are required")
    
    preferences = analyze_preferences(payload["answers"])
    
    # Update session if applicable
    session_id = payload.get("session_id")
    if session_id and session_id in sessions:
        sessions[session_id]["preferences"] = preferences
    
    return {"preferences": preferences}

@app.post("/generate_report")
async def generate_report_endpoint(payload: ReportRequest):
    """Generate a comprehensive learning report"""
    session_id = payload.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Combine provided preferences with session data
    session = sessions[session_id]
    all_preferences = {
        "topic": session.get("topic", ""),
        **session.get("preferences", {}),
        **payload.preferences
    }
    
    # Generate the report
    report_md = await generate_report(session_id, all_preferences)
    
    # Store the report in the session
    sessions[session_id]["report"] = report_md
    
    return {"report": report_md}

@app.patch("/modify_report")
async def modify_report_endpoint(payload: FeedbackRequest):
    """Modify an existing report based on feedback"""
    session_id = payload.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update the report
    updated_md = await modify_report(session_id, payload.feedback)
    
    # Update the session
    sessions[session_id]["report"] = updated_md
    sessions[session_id]["feedback"] = payload.feedback
    
    return {"report": updated_md}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Return session without large data (documents, report)
    session_info = {
        "id": sessions[session_id]["id"],
        "topic": sessions[session_id].get("topic"),
        "has_documents": len(sessions[session_id].get("documents", [])) > 0,
        "has_report": "report" in sessions[session_id],
        "preferences": sessions[session_id].get("preferences", {})
    }
    
    return session_info