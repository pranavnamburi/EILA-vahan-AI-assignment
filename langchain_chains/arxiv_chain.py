from arxiv import Search
from langchain import LLMChain, PromptTemplate
from backend.deps import init_genai

genai = init_genai()

class ArxivChain:
    def __init__(self, max_results: int = 3):
        self.max_results = max_results
        self.llm = genai

    def run(self, topic: str) -> str:
        search_results = Search(query=topic, max_results=self.max_results)
        abstracts = "\n---\n".join(p.summary for p in search_results.results())
        prompt = PromptTemplate(
            input_variables=["abstracts", "topic"],
            template="""
Here are some abstracts on {topic}:
{abstracts}

Summarize the key findings and trends.
"""
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run({"abstracts": abstracts, "topic": topic})