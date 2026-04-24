# backend/rag.py
from pypdf import PdfReader
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import io
import os

load_dotenv(override=True)

# ── Setup ──────────────────────────────────────────────────────────────────────

client     = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc         = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Pinecone v6+: list_indexes() returns objects, not strings
existing_indexes = [idx.name for idx in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=os.getenv("PINECONE_CLOUD", "aws"),
            region=os.getenv("PINECONE_REGION", "us-east-1"),
        ),
    )

index = pc.Index(INDEX_NAME)

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL  = "gpt-4o-mini"
CHUNK_SIZE  = 600
TOP_K       = 4


# ── Step 1: Extract text from PDF ─────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


# ── Step 2: Split into chunks ──────────────────────────────────────────────────

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    chunks  = []
    overlap = 50
    start   = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap
    return chunks


# ── Step 3: Embed text ─────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(input=text, model=EMBED_MODEL)
    return response.data[0].embedding


# ── Step 4: Store PDF in Pinecone ──────────────────────────────────────────────

def store_pdf_in_pinecone(file_bytes: bytes, doc_id: str) -> int:
    text   = extract_text_from_pdf(file_bytes)
    chunks = split_into_chunks(text)

    vectors = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        vectors.append({
            "id":       f"{doc_id}_{i}",
            "values":   embedding,
            "metadata": {"text": chunk, "doc": doc_id},
        })

    for i in range(0, len(vectors), 100):
        index.upsert(vectors=vectors[i : i + 100])

    return len(chunks)


# ── Step 5: Retrieve relevant chunks ──────────────────────────────────────────

def retrieve_context(question: str) -> str:
    question_embedding = get_embedding(question)
    results = index.query(
        vector=question_embedding,
        top_k=TOP_K,
        include_metadata=True,
    )
    return "\n\n".join(
        match["metadata"]["text"] for match in results["matches"]
    )


# ── Step 6: Stream answer ──────────────────────────────────────────────────────

def stream_answer(question: str, history: list[dict]):
    context = retrieve_context(question)

    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant that answers questions strictly based "
            "on the provided PDF context. If the answer is not in the context, "
            "say you don't know.\n\n"
            f"PDF Context:\n{context}"
        ),
    }

    messages = [system_message] + history + [{"role": "user", "content": question}]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        stream=True,
    )

    for chunk in response:
        token = chunk.choices[0].delta.content
        if token:
            yield token
