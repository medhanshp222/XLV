import os
import shutil
import tempfile
import urllib.request
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load API Keys
load_dotenv(override=True)

def extract_metric_from_pdf(pdf_url: str, query: str):
    temp_pdf_path = None
    try:
        print(f"📄 1. Downloading PDF from: {pdf_url}...")
        with urllib.request.urlopen(pdf_url, timeout=60) as response:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                shutil.copyfileobj(response, temp_file)
                temp_pdf_path = temp_file.name

        print(f"📄 2. Loading PDF from temporary file: {temp_pdf_path}...")
        loader = PyPDFLoader(temp_pdf_path)
        documents = loader.load()
        print(f"   -> Loaded {len(documents)} pages.")

        print("✂️  3. Chunking the document...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=400)
        chunks = text_splitter.split_documents(documents)
        print(f"   -> Split into {len(chunks)} searchable chunks.")

        print("🧠 4. Creating the Vector Database (FAISS + Hugging Face Local)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        print("🕵️‍♂️ 5. Analyzing chunks with Gemini...")
        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert ESG auditor. Review the provided document excerpts and answer the user's question. If the exact metric is not in the text, say 'Metric not found.'\n\nExcerpts:\n{context}"),
            ("human", "{input}")
        ])

        document_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, document_chain)

        response = rag_chain.invoke({"input": query})
        return response["answer"]
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

# --- Run the Script ---
if __name__ == "__main__":
    target_url = "https://www.example.com/sample.pdf"

    audit_query = "What is the 'Total Scope 1 and Scope 2 emission intensity in terms of physical output' for FY 2025-26? Return just the number and the unit."

    answer = extract_metric_from_pdf(target_url, audit_query)
    print("\n" + "=" * 50)
    print("🎯 EXTRACTION RESULT:")
    print(answer)
    print("=" * 50)