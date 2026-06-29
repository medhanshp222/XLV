import os
import shutil
import tempfile
import requests
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

_CURRENT_TEMP_PDF_PATH: str | None = None


def read_sustainability_report_by_page(page_number: int):
    if not _CURRENT_TEMP_PDF_PATH or not os.path.exists(_CURRENT_TEMP_PDF_PATH):
        return ""

    loader = PyPDFLoader(_CURRENT_TEMP_PDF_PATH)
    documents = loader.load()
    if page_number < 0 or page_number >= len(documents):
        return ""
    return documents[page_number].page_content or ""


def extract_all_pdf_pages():
    if not _CURRENT_TEMP_PDF_PATH or not os.path.exists(_CURRENT_TEMP_PDF_PATH):
        return []

    loader = PyPDFLoader(_CURRENT_TEMP_PDF_PATH)
    documents = loader.load()
    return [
        {"page": index + 1, "text": document.page_content or ""}
        for index, document in enumerate(documents)
    ]


def extract_metric_from_pdf(pdf_url: str, query: str):
    global _CURRENT_TEMP_PDF_PATH
    temp_pdf_path = None
    try:
        if _CURRENT_TEMP_PDF_PATH and os.path.exists(_CURRENT_TEMP_PDF_PATH):
            os.remove(_CURRENT_TEMP_PDF_PATH)
        _CURRENT_TEMP_PDF_PATH = None

        print(f"📄 1. Downloading PDF from: {pdf_url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
        with requests.get(pdf_url, headers=headers, timeout=30, stream=True) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_pdf_path = temp_file.name
                _CURRENT_TEMP_PDF_PATH = temp_pdf_path

        print(f"📄 2. Loading PDF from temporary file: {temp_pdf_path}...")
        loader = PyPDFLoader(temp_pdf_path)
        documents = loader.load()
        print(f"   -> Loaded {len(documents)} pages.")

        print("✂️  3. Chunking the document...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=700)
        chunks = text_splitter.split_documents(documents)
        print(f"   -> Split into {len(chunks)} searchable chunks.")

        # ADD THIS SAFETY NET:
        if len(chunks) == 0:
            print("⚠️ ERROR: No text found in this PDF (likely scanned images). Skipping...")
            return "Metric not found."

        print("🧠 4. Creating the Vector Database (FAISS + Hugging Face Local)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        print("🕵️‍♂️ 5. Analyzing chunks with Gemini...")
        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert ESG auditor. Review the provided document excerpts and answer the user's question. If the exact metric is not in the text, say 'Metric not found.'\n\nExcerpts:\n{context}"),
            ("human", "{input}")
        ])

        document_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, document_chain)

        response = rag_chain.invoke({"input": query})
        source_docs = response.get("context", []) or []
        pages = list(
            set(
                [
                    doc.metadata.get("page", 0) + 1
                    for doc in source_docs
                    if getattr(doc, "metadata", None) and "page" in doc.metadata
                ]
            )
        )
        pages.sort()
        return f"{response['answer']}\n[Source Pages: {pages}]"
    finally:
        # Keep the downloaded PDF available for page-level precision harvest.
        pass

# --- Run the Script ---
if __name__ == "__main__":
    target_url = "https://www.example.com/sample.pdf"

    audit_query = "What is the 'Water intensity in terms of physical output' for the current year? Return just the number and the unit."

    answer = extract_metric_from_pdf(target_url, audit_query)
    print("\n" + "=" * 50)
    print("🎯 EXTRACTION RESULT:")
    print(answer)
    print("=" * 50)