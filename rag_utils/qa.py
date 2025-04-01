import faiss
import numpy as np
import os
from dotenv import load_dotenv
import cohere

load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)


def get_general_answers(question,history):
     # Call Cohere's chat model with history
    answer = response = co.chat(
            model="command-r7b-12-2024",
            message=question,
            chat_history=[{"role": msg["role"], "message": msg["content"]} for msg in history],
            temperature=0.3,
            connectors=[{"id": "web-search"}]
        )
    return answer.text
def load_faiss_index(index_path='vector_store/index.faiss'):
    return faiss.read_index(index_path)

def embed_question(question):
    response = co.embed(texts=[question], model="embed-english-v3.0",input_type="search_query")
    return np.array(response.embeddings).astype("float32")

def search_similar_chunks(question_embedding, k=5):
    index = load_faiss_index()
    distances, indices = index.search(question_embedding, k)
    return indices[0]  # return top-k indices

# Dummy chunks for now — in a real case, you'd load them from a DB or file
def get_all_chunks(file_path="vector_store/chunks.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            chunks = f.read().split("====chunk====")
            return [chunk.strip() for chunk in chunks if chunk.strip()]
    except FileNotFoundError:
        print(f"Chunk file not found at {file_path}")
        return []

def build_prompt(conversation):
    prompt = ""
    for msg in conversation:
        role = msg["role"].capitalize()
        message = msg["message"]
        prompt += f"{role}: {message}\n"
    prompt += "Assistant:"
    return prompt

def build_prompt(question, top_chunks,history=[]):
    context = "\n".join(top_chunks)
    prompt = f"""Answer the question based on the following context:\n\n{context}\n\nQuestion: {question}\nAnswer:"""
    
    if history:
        prompt += "Conversation so far:\n"
        for msg in history:
            role = msg['role'].capitalize()
            message = msg['message']
            prompt += f"{role}: {message}\n"

    prompt += f"User: {question}\nAssistant:"  # continue from user question
    return prompt

def generate_answer(prompt,history=[]):
    response = co.chat(
        model="command-r7b-12-2024",
        chat_history=history,
        message=prompt,
        temperature=0.2,
        citation_quality='fast',
        seed=42,
        stop_sequences = ["STOP", "End here","Additionaly","Also"],
    )
    print(response.text.strip())
    return response.text.strip()

def answer_question(question,history=[]):
    embedding = embed_question(question)
    top_k_indices = search_similar_chunks(embedding)

    all_chunks = get_all_chunks()
    top_chunks = [all_chunks[i] for i in top_k_indices if i < len(all_chunks)]

    prompt = build_prompt(question, top_chunks,history)
    answer = generate_answer(prompt,history)
    return answer
