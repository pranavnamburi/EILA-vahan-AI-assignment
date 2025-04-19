from youtube_transcript_api import YouTubeTranscriptApi
from langchain import LLMChain, PromptTemplate
from backend.deps import init_genai

genai = init_genai()

class TranscriptChain:
    def __init__(self):
        self.llm = genai

    def run(self, video_id: str) -> str:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(seg['text'] for seg in transcript)
        prompt = PromptTemplate(
            input_variables=["transcript_text"],
            template="""
Below is a transcript from a video:
{transcript_text}

Provide a concise summary of this content.
"""
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run({"transcript_text": text})