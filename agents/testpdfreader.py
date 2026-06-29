import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load API Keys
load_dotenv(override=True)

def extract_metric_from_pdf(local_pdf_path: str, query: str):
    print(f"📄 1. Loading local PDF file: {local_pdf_path}...")
    
    # Check if file actually exists before trying to load it
    if not os.path.exists(local_pdf_path):
        return f"Error: File not found at {local_pdf_path}"

    loader = PyPDFLoader(local_pdf_path)
    documents = loader.load()
    print(f"   -> Loaded {len(documents)} pages.")

    print("✂️  2. Chunking the document...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=400)
    chunks = text_splitter.split_documents(documents)
    print(f"   -> Split into {len(chunks)} searchable chunks.")

    print("🧠 3. Creating the Vector Database (FAISS + Hugging Face Local)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_store = FAISS.from_documents(chunks, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    print("🕵️‍♂️ 4. Analyzing chunks with Gemini...")
    # FIXED: Changed model to 2.5
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert ESG auditor. Review the provided document excerpts and answer the user's question. If the exact metric is not in the text, say 'Metric not found.'\n\nExcerpts:\n{context}"),
        ("human", "{input}")
    ])

    document_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)

    response = rag_chain.invoke({"input": query})
    return response["answer"]

# --- Run the Script ---
if __name__ == "__main__":
    target_path = "/Users/medhanshpindi/Desktop/XLV/XLV/agents/JSL_Sustainability_Report_New_2024_compressed.pdf"

    # NOTE: I added the "not energy" guardrail here just in case this sample PDF also has confusing tables!
    audit_query = (
        "What is the 'Water intensity in terms of physical output' ? Return just the number and the unit."
    )

    answer = extract_metric_from_pdf(target_path, audit_query)
    print("\n" + "=" * 50)
    print("🎯 EXTRACTION RESULT:")
    print(answer)
    print("=" * 50)