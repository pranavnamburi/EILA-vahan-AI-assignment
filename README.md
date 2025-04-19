
# EILA - Enhanced Interactive Learning Assistant

EILA is an AI-powered learning assistant that creates personalized educational reports on any topic. It combines multi-source research with customized content generation to deliver tailored learning experiences.

## Setup Instructions

### Prerequisites

- Python 3.8+
- API keys:
  - Google Gemini API key (for AI content generation)
  - SerpAPI key (for web and YouTube searches)

### Installation

#### Option 1: Direct Installation

1. Clone the repository

```bash
git clone https://github.com/pranavnamburi/EILA-vahan-AI-assignment
cd EILA-vahan-AI-assignment
```

2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory with your API keys:

```
SERPAPI_API_KEY=your_serpapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Option 2: Using Docker

1. Clone the repository

```bash
git clone https://github.com/pranavnamburi/EILA-vahan-AI-assignment
cd EILA-vahan-AI-assignment
```

2. Create a .env file with your API keys (same as above)
3. Build the Docker image

```bash
docker build -t eila-app .
```

4. Run the container

```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env eila-app
```

### Running the Application

#### Without Docker

1. Start the backend server

```bash
cd eila
uvicorn backend.app:app --reload
```

2. In a separate terminal, start the frontend

```bash
cd eila
streamlit run frontend/app.py
```

3. Access the application at http://localhost:8501

#### With Docker

After running the Docker container with the command above, both the backend and frontend will start automatically. Access the application at http://localhost:8501

Note: For data persistence between container restarts, you can mount a volume:

```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env -v ./indexes:/app/indexes eila-app
```

## System Architecture

### Components

- **Frontend**: Streamlit-based user interface that guides users through the learning process
- **Backend**: FastAPI server that handles research, content generation, and data persistence
- **Vector Database**: FAISS for storing and retrieving research content
- **External APIs**:
  - Google Gemini API for AI content generation
  - SerpAPI for web and YouTube searches
  - arXiv API for academic papers

### Data Flow

1. User inputs topic and objectives via the Streamlit interface
2. Backend performs multi-source research and indexes the content
3. User provides preferences for personalization
4. Backend generates a tailored report using the indexed content
5. User can download or request modifications to the report

## Research Methodology

EILA employs a comprehensive research approach across multiple sources:

1. **Web Search**: Uses SerpAPI to retrieve relevant web content about the topic
2. **Academic Papers**: Queries arXiv for scholarly articles and extracts their abstracts
3. **Video Content**: Searches YouTube for educational videos and extracts transcript text

All research content is:

- Processed with a text splitter to create manageable chunks
- Embedded using HuggingFace embeddings (all-MiniLM-L6-v2)
- Indexed in a FAISS vector store for efficient retrieval
- Tagged with source metadata for proper attribution

## Personalization Approach

EILA adapts content to the user's unique needs through:

1. **Preference Collection**: Gathers information about:

   - Familiarity with the topic (None, Beginner, Intermediate, Advanced)
   - Preferred learning format (Text, Diagrams, Code examples, etc.)
   - Desired depth of content (Overview, Moderate depth, In-depth, Expert)
   - Specific areas of interest
   - Available study time
2. **Content Adaptation**:

   - Adjusts technical complexity based on user's knowledge level
   - Includes visuals, code examples, or video references according to preferences
   - Modifies content depth based on expertise and available time
   - Focuses on user-specified aspects of the topic
3. **AI-Powered Analysis**: Converts user responses into specific content parameters like depth level, visual inclusion, and time allocation

## Report Generation and Modification

### Generation Process

1. **Contextual Retrieval**: Uses a ContextualCompressionRetriever with LLMChainExtractor to extract relevant information from the research index
2. **Structured Content Creation**: Generates various sections:

   - Topic overview and learning objectives
   - Key concepts
   - Main content sections (dynamically determined)
   - Code examples (when requested)
   - Visual aids (when requested)
   - Assessment questions
   - Additional resources
3. **Output Formats**: Provides reports in:

   - Markdown format (for web viewing)
   - PDF (for downloading and offline access)

### Modification Implementation

1. User submits feedback on the generated report
2. The system analyzes the feedback to identify specific areas for improvement
3. A specialized LLMChain generates an updated version addressing the feedback
4. The new report maintains overall quality while incorporating requested changes

## Limitations and Future Improvements

### Current Limitations

1. **API Rate Limits**: SerpAPI and Gemini API have usage quotas that can restrict functionality
2. **Research Breadth**: Limited to web content, arXiv papers, and YouTube videos
3. **Language Support**: Currently optimized for English content only
4. **Content Formatting**: PDF generation has limited styling capabilities

### Future Improvements

1. **Enhanced Research**:

   - Integration with additional academic databases
   - Book and e-learning platform content inclusion
   - Improved PDF generation with better formatting
2. **Interactive Features**:

   - Interactive quizzes and exercises
   - Spaced repetition learning modules
   - Collaborative learning capabilities
3. **Technical Enhancements**:

   - Persistent database for user sessions and reports
   - Improved rate limiting and caching for API calls
   - Advanced visualization generation
