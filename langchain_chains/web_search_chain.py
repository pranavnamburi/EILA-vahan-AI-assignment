from serpapi import GoogleSearch
from langchain import LLMChain, PromptTemplate
from backend.deps import init_genai

# Initialize Gemini client
genai = init_genai()

class WebSearchChain:
    def __init__(self, serp_api_key: str):
        self.search = GoogleSearch({"api_key": serp_api_key})
        self.llm = genai

    def run(self, query: str, k: int = 5) -> str:
        results = self.search.get_dict().get("organic_results", [])[:k]
        snippets = "\n".join(r.get("snippet", "") for r in results)
        prompt = PromptTemplate(
            input_variables=["snippets", "query"],
            template="""
Given these web snippets:
{snippets}

Answer: {query}
"""
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run({"snippets": snippets, "query": query})