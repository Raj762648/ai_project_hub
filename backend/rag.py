from __future__ import annotations
import os
import tempfile
from typing import Generator

from dotenv import load_dotenv

# ── LangChain v1 imports ────────────────────────────────────────────────────
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── Pinecone (direct SDK for index management only) ─────────────────────────
from pinecone import Pinecone, ServerlessSpec

load_dotenv(override=True)

# ── Configuration ────────────────────────────────────────────────────────────
INDEX_NAME  = os.environ["PINECONE_INDEX_NAME"]
NAMESPACE   = "default"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL  = "gpt-4o-mini"
TOP_K       = 6   # MMR candidate pool; final answer uses best k=4

# ── Pinecone index bootstrap ─────────────────────────────────────────────────
_pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

if INDEX_NAME not in [idx.name for idx in _pc.list_indexes()]:
    _pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=os.getenv("PINECONE_CLOUD", "aws"),
            region=os.getenv("PINECONE_REGION", "us-east-1"),
        ),
    )

# ── LangChain components ─────────────────────────────────────────────────────
_embeddings = OpenAIEmbeddings(model=EMBED_MODEL)

_llm = ChatOpenAI(
    model=CHAT_MODEL,
    temperature=0,       # deterministic, fact-grounded answers
    streaming=True,
)

_vector_store = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=_embeddings,
    namespace=NAMESPACE,
)

# Maximal Marginal Relevance reduces repetitive chunks from the same passage
_retriever = _vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4,             # chunks returned to the prompt
        "fetch_k": TOP_K * 3,
        "lambda_mult": 0.7, # 0 = max diversity · 1 = max relevance
    },
)

# ── Text splitter ─────────────────────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,                              # wider overlap = fewer cut sentences
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    length_function=len,
)

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM = """\
You are a thorough document analyst. Your ONLY knowledge source is the PDF \
excerpts in <context>. Generate comprehensive, well-structured Markdown \
answers — every statement must be grounded in the provided excerpts.

## Formatting
- **Structure**: Open with a `###` title, use `####` sections and `#####` sub-sections
- **Emphasis**: `**bold**` key terms/figures, `*italics*` for definitions
- **Lists**: bullets (`-`) for 3+ related items, numbered (`1.`) for sequences
- **Technical values**: wrap in `backticks`
- **Direct quotes**: `> "phrase" — [Excerpt N]` blockquote format
- **End**: `---` divider then a `### Summary` of 3–5 sentences

## Content
- **Exhaust the context**: extract every relevant detail — elaborate, don't truncate
- **Cite everything**: bold inline citations after each claim — **[Excerpt 2]** or **[Excerpt 1][Excerpt 3]**
- **Missing info**: write *"That information is not available in the uploaded document."* — never guess
- **Multi-part questions**: each sub-question gets its own `##` heading; mark unanswerable ones explicitly
- **Contradictions**: surface them under a `### ⚠️ Conflicting Information` sub-section
- **Never invent**: no names, numbers, dates, or facts beyond what the excerpts state

<context>
{context}
</context>"""

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])


# ── Internal helpers ──────────────────────────────────────────────────────────

def _format_docs(docs: list[Document]) -> str:
    """Render retrieved chunks with numbered separators so the LLM can cite them."""
    return "\n\n---\n\n".join(
        f"[Excerpt {i}]\n{doc.page_content.strip()}"
        for i, doc in enumerate(docs, 1)
    )


def _to_lc_messages(history: list[dict]) -> list[HumanMessage | AIMessage]:
    """Convert plain {"role": ..., "content": ...} dicts to LangChain message objects."""
    mapping = {"user": HumanMessage, "assistant": AIMessage}
    return [
        mapping[msg["role"]](content=msg["content"])
        for msg in history
        if msg.get("role") in mapping
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def store_pdf_in_pinecone(file_bytes: bytes, doc_id: str) -> int:
    """
    Ingest *file_bytes* as a PDF into Pinecone.

    Steps:
      1. Write bytes to a temp file (PyPDFLoader needs a path).
      2. Load page-by-page with PyPDFLoader (preserves page metadata).
      3. Split with RecursiveCharacterTextSplitter.
      4. Clear the namespace, then upsert all chunks.

    Returns the number of chunks stored.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path, mode="page")   # one Document per page
        pages  = loader.load()
    finally:
        os.unlink(tmp_path)

    # Tag every chunk so you can filter by document later
    for page in pages:
        page.metadata["doc"] = doc_id

    chunks = _splitter.split_documents(pages)

    # Wipe existing vectors before storing the new document
    try:
        _pc.Index(INDEX_NAME).delete(delete_all=True, namespace=NAMESPACE)
    except Exception as exc:
        print(f"[store_pdf] namespace clear warning: {exc}")

    _vector_store.add_documents(chunks)
    return len(chunks)


def stream_answer(question: str, history: list[dict]) -> Generator[str, None, None]:
    """
    Retrieve the most relevant chunks for *question*, build a grounded prompt
    with conversation *history*, and stream the answer token-by-token.

    *history* format: [{"role": "user"|"assistant", "content": "..."}]
    """
    lc_history = _to_lc_messages(history)

    # LCEL chain: retrieve → format → prompt → LLM → parse
    chain = (
        {
            "context":  _retriever | _format_docs,
            "question": RunnablePassthrough(),
            "history":  RunnableLambda(lambda _: lc_history),
        }
        | _prompt
        | _llm
        | StrOutputParser()
    )

    yield from chain.stream(question)
