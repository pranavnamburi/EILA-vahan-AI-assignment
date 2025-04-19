import os
from typing import Dict, List, Optional
from langchain import PromptTemplate, LLMChain
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from backend.deps import init_genai, get_genai_llm
from backend.indexing import get_session_index

# Initialize the generative AI module for direct API calls
genai = init_genai()
# Get a LangChain-compatible LLM for integration with LangChain components
llm = get_genai_llm()

# Templates for different report sections
OVERVIEW_TEMPLATE = """
# Overview of {topic}

{overview_text}

## Learning Objectives
{objectives_text}

## Key Concepts
{key_concepts}
"""

SECTION_TEMPLATE = """
You are creating an educational section for a learning report on {topic}.
The user has the following preferences:
- Knowledge level: {knowledge_level}
- Preferred depth: Level {depth} (1=basic, 3=advanced)
- Focus areas: {focus_area}

Based on these research documents:
{context}

Create a detailed and informative section about: {section_title}
Make sure to:
1. Use clear explanations appropriate for the user's knowledge level
2. Include specific examples and applications
3. Reference sources where appropriate using footnotes [1] style
4. Use markdown formatting for headings, bullet points, etc.
5. Don't exceed the appropriate depth level for this user

Section:
"""

VISUAL_TEMPLATE = """
Based on the following content about {topic}:
{context}

Create a text description of a diagram that would help visualize the concept of {visual_concept}.
The diagram should be clear and educational, suitable for a {knowledge_level} level learner.
Use markdown to describe what the diagram should show. Include labels, arrows, and components that should be included.

Diagram Description:
"""

CODE_EXAMPLE_TEMPLATE = """
Create a practical code example that demonstrates {concept} in {topic}.
This should be suitable for someone with {knowledge_level} knowledge level.
Based on the following information:
{context}

The code should:
1. Be well-commented to explain what each section does
2. Be complete enough to demonstrate the concept clearly
3. Include sample output if applicable
4. Use best practices

```{language}
# Your code here
```

Explanation:
"""

ADDITIONAL_RESOURCES_TEMPLATE = """
Based on the research materials:
{context}

Create a list of 3-5 additional learning resources for someone interested in {topic}.
The person has a {knowledge_level} level of familiarity with the subject.
For each resource, include:
1. The title/name
2. A brief description (1-2 sentences)
3. Why it's valuable for further learning
4. Type of resource (book, course, video, etc.)

Format using markdown with clear headings and bullet points.
"""

ASSESSMENT_TEMPLATE = """
Create 3-5 assessment questions to help the learner check their understanding of {topic}.
The questions should be suitable for someone with {knowledge_level} knowledge level.
Based on the following materials:
{context}

Include a mix of question types (multiple choice, short answer, etc.)
Provide answers or solution hints after each question.
Format everything with clear markdown.
"""

async def generate_report(session_id: str, preferences: dict) -> str:
    """Generate a comprehensive learning report based on research and user preferences."""
    # Get user preferences and research data
    vectorstore = get_session_index(session_id)
    if not vectorstore:
        return "Error: No research data found for this session."
    
    # Extract preferences
    topic = preferences.get("topic", "the requested topic")
    knowledge_level = preferences.get("familiarity", "Beginner")
    depth_level = preferences.get("depth_level", 2)
    focus_area = preferences.get("focus_area", "general understanding")
    include_visuals = preferences.get("include_visuals", False)
    include_code = preferences.get("include_code", False)
    include_videos = preferences.get("include_videos", False)
    
    # Create a retriever with contextual compression
    compressor = LLMChainExtractor.from_llm(llm)
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
    )
    
    # Generate the overview section
    overview_context = retriever.get_relevant_documents(f"overview of {topic}")
    overview_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["topic", "context"],
            template=f"Create a comprehensive overview of {{topic}} based on this research: {{context}}"
        )
    )
    overview_text = overview_chain.run(topic=topic, context=overview_context)
    
    # Generate learning objectives
    objectives_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["topic", "knowledge_level", "focus_area"],
            template=f"Create 3-5 clear learning objectives for {{topic}} at a {{knowledge_level}} level, focusing on {{focus_area}}."
        )
    )
    objectives_text = objectives_chain.run(
        topic=topic, 
        knowledge_level=knowledge_level,
        focus_area=focus_area
    )
    
    # Generate key concepts
    concepts_context = retriever.get_relevant_documents(f"key concepts in {topic}")
    concepts_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["topic", "context", "knowledge_level"],
            template=f"List and briefly explain 5-7 key concepts in {{topic}} suitable for a {{knowledge_level}} level, based on: {{context}}"
        )
    )
    key_concepts = concepts_chain.run(
        topic=topic,
        context=concepts_context,
        knowledge_level=knowledge_level
    )
    
    # Determine main content sections
    sections_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["topic", "focus_area"],
            template=f"List 3-5 important subtopics or sections for learning about {{topic}}, focusing on {{focus_area}}. Return only the section titles separated by commas."
        )
    )
    sections_text = sections_chain.run(topic=topic, focus_area=focus_area)
    sections = [s.strip() for s in sections_text.split(",")]
    
    # Build report with all sections
    markdown = f"# Learning Report: {topic}\n\n"
    
    # Add overview section
    markdown += OVERVIEW_TEMPLATE.format(
        topic=topic,
        overview_text=overview_text,
        objectives_text=objectives_text,
        key_concepts=key_concepts
    )
    
    # Generate content for each section
    for section_title in sections:
        section_context = retriever.get_relevant_documents(f"{section_title} in {topic}")
        section_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["topic", "section_title", "context", "knowledge_level", "depth", "focus_area"],
                template=SECTION_TEMPLATE
            )
        )
        section_content = section_chain.run(
            topic=topic,
            section_title=section_title,
            context=section_context,
            knowledge_level=knowledge_level,
            depth=depth_level,
            focus_area=focus_area
        )
        markdown += f"\n\n## {section_title}\n\n{section_content}"
        
        # Add visual aid if requested
        if include_visuals:
            visual_chain = LLMChain(
                llm=llm,
                prompt=PromptTemplate(
                    input_variables=["topic", "visual_concept", "context", "knowledge_level"],
                    template=VISUAL_TEMPLATE
                )
            )
            visual_content = visual_chain.run(
                topic=topic,
                visual_concept=section_title,
                context=section_context,
                knowledge_level=knowledge_level
            )
            markdown += f"\n\n### Visual Aid: {section_title}\n\n{visual_content}"
        
        # Add code example if requested
        if include_code:
            # Determine appropriate programming language for the topic
            lang_chain = LLMChain(
                llm=llm,
                prompt=PromptTemplate(
                    input_variables=["topic"],
                    template="What would be the most appropriate programming language to demonstrate concepts in {topic}? Answer with just the language name (e.g., 'Python', 'JavaScript')."
                )
            )
            language = lang_chain.run(topic=topic).strip()
            
            code_chain = LLMChain(
                llm=llm,
                prompt=PromptTemplate(
                    input_variables=["topic", "concept", "context", "knowledge_level", "language"],
                    template=CODE_EXAMPLE_TEMPLATE
                )
            )
            code_content = code_chain.run(
                topic=topic,
                concept=section_title,
                context=section_context,
                knowledge_level=knowledge_level,
                language=language
            )
            markdown += f"\n\n### Code Example: {section_title}\n\n{code_content}"
    
    # Add assessment questions
    assessment_context = retriever.get_relevant_documents(f"assessment questions for {topic}")
    assessment_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["topic", "context", "knowledge_level"],
            template=ASSESSMENT_TEMPLATE
        )
    )
    assessment_content = assessment_chain.run(
        topic=topic,
        context=assessment_context,
        knowledge_level=knowledge_level
    )
    markdown += f"\n\n## Check Your Understanding\n\n{assessment_content}"
    
    # Add additional resources
    resources_context = retriever.get_relevant_documents(f"learning resources for {topic}")
    resources_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["topic", "context", "knowledge_level"],
            template=ADDITIONAL_RESOURCES_TEMPLATE
        )
    )
    resources_content = resources_chain.run(
        topic=topic,
        context=resources_context,
        knowledge_level=knowledge_level
    )
    markdown += f"\n\n## Additional Resources\n\n{resources_content}"
    
    # Add references section
    markdown += "\n\n## References\n\n"
    references_set = set()
    for doc in vectorstore.as_retriever().get_relevant_documents(topic):
        source = doc.metadata.get("source", "Unknown source")
        if source not in references_set:
            references_set.add(source)
            markdown += f"- {source}\n"
    
    return markdown

async def modify_report(session_id: str, feedback: dict) -> str:
    """Modify the report based on user feedback."""
    vectorstore = get_session_index(session_id)
    if not vectorstore:
        return "Error: No research data found for this session."
    
    feedback_text = feedback.get("text", "")
    
    # Analyze what aspects need modification
    analysis_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["feedback"],
            template="Analyze this feedback for a learning report: {feedback}\n\nIdentify specific aspects that need modification and what changes are requested. Format your response as a JSON object with keys 'aspects' (array of sections to modify) and 'requests' (array of requested changes)."
        )
    )
    analysis_result = analysis_chain.run(feedback=feedback_text)
    
    # Generate modified report based on feedback analysis
    context_docs = vectorstore.as_retriever(search_kwargs={"k": 10}).get_relevant_documents(feedback_text)
    
    modification_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["feedback", "context", "session_id"],
            template="""
Based on this user feedback:
{feedback}

And these relevant research materials:
{context}

Create an updated version of the learning report for session {session_id}.
Make specific improvements addressing the feedback while maintaining the overall structure and quality of the report.
Format the response as complete markdown document suitable for educational purposes.
            """
        )
    )
    
    updated_report = modification_chain.run(
        feedback=feedback_text,
        context=context_docs,
        session_id=session_id
    )
    
    return updated_report