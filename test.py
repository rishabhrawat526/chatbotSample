import cohere
from cohere.types import EmbeddingType
import os
from dotenv import load_dotenv
import numpy as np
import fitz
import faiss
load_dotenv()

api_key = os.getenv('COHERE_API_KEY')
co = cohere.Client(api_key)

# response = co.embed(
#     texts=["hello", "world"],
#     model="embed-english-v3.0",
#     input_type="search_document",

# )

# print(type(response.embeddings))

def extract_text_from_pdf():
    doc = fitz.open("invoice.pdf")
    print(type(doc))
    text=""
    for page in doc:
        print(page)
        text+=page.get_text()
    return text


def chunk_text(text,chunk_size=500,overlap=100):
    chunks=[]
    start = 0
    while start <len(text):
        end = min(start+chunk_size,len(text))
        chunks.append(text[start:end])
        start+=chunk_size - overlap    
        return chunks


def store_embeddings_faiss(embeddings, save_path='vector_store22/index.faiss'):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))
    print(index.ntotal)
    print(index.is_trained)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    faiss.write_index(index, save_path)

    print(f"Vector index saved to {save_path}")
    return index

def embed_chunks(chunks):
    response = co.embed(texts=chunks,model="embed-english-v3.0",input_type="search_document")
    return response.embeddings

text = extract_text_from_pdf()
chunks = chunk_text(text)
embeddings = embed_chunks(chunks)
index = store_embeddings_faiss(embeddings)
print(type(text))
print(type(chunks))
print(len(chunks))
print(len(embeddings))
print(index)

