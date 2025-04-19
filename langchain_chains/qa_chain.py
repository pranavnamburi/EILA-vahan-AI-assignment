from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings    
from backend.deps import init_genai

# Initialize embeddings & LLM
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

llm = init_genai()

class QAChain:
    def __init__(self, faiss_index_path: str):
        self.db = FAISS.load_local(faiss_index_path, embeddings)
        self.chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.db.as_retriever()
        )

    def run(self, question: str) -> str:
        return self.chain.run(question)