import fitz
import cohere
import faiss
import os
import numpy as np
from dotenv import load_dotenv
load_dotenv()


COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)


def extract_text_from_pdf(pdf_path):
    print(pdf_path)
    file_ext = pdf_path.split('.')[-1].lower()
    if file_ext not in ['pdf','txt']:
        return "Unsupported file format. Please upload a PDF or TXT file.", 400
    
    text=""
    if file_ext == "pdf":
        doc = fitz.open(pdf_path)
        for page in doc:
            # no if pages in the document
            text+=page.get_text()
    elif file_ext == "txt":
        with open(pdf_path, "r", encoding="utf-8") as file:
            text = file.read() 
    # class pymupdf.document
    
    print(file_ext)
    print(text)
    return text


def chunk_text(text,chunk_size=500,overlap=100):
    chunks=[]
    start = 0
    while start <len(text):
        end = min(start+chunk_size,len(text))
        chunks.append(text[start:end])
        start+=chunk_size - overlap   

    with open("vector_store/chunks.txt", "w", encoding="utf-8") as f:
        f.write("====chunk====".join(chunks)) 
    print("===chunks=== processed")
    return chunks


def embed_chunks(chunks):
    response = co.embed(texts=chunks,model="embed-english-v3.0",input_type="search_document")
    return response.embeddings


def store_embeddings_faiss(embeddings, save_path='vector_store/index.faiss'):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    faiss.write_index(index, save_path)

    print(f"Vector index saved to {save_path}")
    return index

def process_pdf_to_vectors(pdf_path):
    print("Reading PDF...")
    text = extract_text_from_pdf(pdf_path)
    print(text)
    print("Chunking text...")
    chunks = chunk_text(text)

    print(f"Generated {len(chunks)} chunks. Embedding...")
    embeddings = embed_chunks(chunks)

    print("Storing in vector DB...")
    index = store_embeddings_faiss(embeddings)

    print("Done.")
    return index  # optional: return for debugging or querying