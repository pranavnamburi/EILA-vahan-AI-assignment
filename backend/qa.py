from typing import Dict, List
from backend.deps import init_genai

genai = init_genai()

def get_clarification_questions(answers: dict) -> list[dict]:
    """Generate a set of clarification questions based on the topic and objectives."""
    topic = answers.get('topic', 'this topic')
    
    questions = [
        {"id": "familiarity", "question": f"How familiar are you with {topic}?", 
         "options": ["None", "Beginner", "Intermediate", "Advanced"]},
        
        {"id": "format", "question": "Which learning format do you prefer?", 
         "options": ["Text", "Diagrams", "Code examples", "Interactive elements", "Videos"]},
        
        {"id": "depth", "question": "How detailed would you like the content to be?", 
         "options": ["Overview", "Moderate depth", "In-depth", "Expert level"]},
        
        {"id": "focus", "question": f"What aspect of {topic} interests you most?", 
         "input_type": "text"},
        
        {"id": "time", "question": "How much time do you have to study this topic?", 
         "options": ["15 minutes", "30 minutes", "1 hour", "Multiple sessions"]}
    ]
    
    return questions

def analyze_preferences(answers: Dict) -> Dict:
    """
    Analyze user preferences to determine customization parameters
    for the report generation.
    """
    preferences = {
        "depth_level": 1,  # Default: moderate depth
        "include_visuals": False,
        "include_code": False,
        "include_videos": False,
        "session_time": 30,  # Default: 30 minutes
    }
    
    # Set depth based on familiarity and requested depth
    familiarity = answers.get("familiarity", "Beginner")
    depth = answers.get("depth", "Moderate depth")
    
    if familiarity == "None" or familiarity == "Beginner":
        preferences["depth_level"] = 1  # Basic explanation
    elif familiarity == "Intermediate":
        preferences["depth_level"] = 2  # More detailed
    else:  # Advanced
        preferences["depth_level"] = 3  # Technical details
    
    # Adjust based on explicitly requested depth
    if depth == "Overview":
        preferences["depth_level"] = max(1, preferences["depth_level"] - 1)
    elif depth == "In-depth":
        preferences["depth_level"] = min(3, preferences["depth_level"] + 1)
    elif depth == "Expert level":
        preferences["depth_level"] = 3
    
    # Set content format preferences
    format_pref = answers.get("format", "Text")
    if format_pref == "Diagrams":
        preferences["include_visuals"] = True
    elif format_pref == "Code examples":
        preferences["include_code"] = True
    elif format_pref == "Videos":
        preferences["include_videos"] = True
    
    # Set time preference
    time_pref = answers.get("time", "30 minutes")
    if time_pref == "15 minutes":
        preferences["session_time"] = 15
    elif time_pref == "1 hour":
        preferences["session_time"] = 60
    elif time_pref == "Multiple sessions":
        preferences["session_time"] = 120
    
    # Add specific focus area if provided
    if "focus" in answers and answers["focus"]:
        preferences["focus_area"] = answers["focus"]
    
    return preferences