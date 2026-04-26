import io
import json
from collections import defaultdict
from datetime import datetime

import requests
import xml.etree.ElementTree as ET
from pypdf import PdfReader

from langchain.agents import create_agent                      # ← correct in langchain 1.x
from langgraph.checkpoint.memory import MemorySaver            # ← replaces ConversationBufferWindowMemory
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# ── Shared objects ─────────────────────────────────────────────────────────────
openai_api_key = os.environ["OPENAI_API_KEY"]
openai_embedding_model = os.environ["EMBEDDING_MODEL"]
arxiv_max_results = 8
top_k_papers = 2
top_k_chunks = 6

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=openai_api_key,
)

embeddings_model = OpenAIEmbeddings(
    model=openai_embedding_model,
    api_key=openai_api_key,
)

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

# One shared MemorySaver — sessions are isolated by thread_id
_checkpointer = MemorySaver()

# In-memory raw history for the /history API endpoint
_raw_history: dict[str, list[dict]] = defaultdict(list)

# FAISS store — rebuilt each request (demo: no persistence needed)
_faiss_store: FAISS | None = None

ARXIV_NS = "http://www.w3.org/2005/Atom"


# ── Tool 1 — Search arXiv ──────────────────────────────────────────────────────

@tool
def search_arxiv(query: str) -> str:
    """
    Search arXiv for academic papers matching a query.
    Returns a JSON list with id, title, summary (300 chars), age_days, and pdf_url.
    Call this 2-3 times with different query angles to find the best papers.
    """
    try:
        resp = requests.get(
            "http://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{query}",
                "max_results": arxiv_max_results,
                "sortBy": "relevance",
            },
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        return json.dumps({"error": str(e)})

    root = ET.fromstring(resp.text)
    now = datetime.utcnow()
    papers = []

    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        arxiv_id = entry.findtext(f"{{{ARXIV_NS}}}id", "").strip().split("/abs/")[-1]
        title   = entry.findtext(f"{{{ARXIV_NS}}}title", "").replace("\n", " ").strip()
        summary = entry.findtext(f"{{{ARXIV_NS}}}summary", "").replace("\n", " ").strip()
        pub_str = entry.findtext(f"{{{ARXIV_NS}}}published", "")
        try:
            age_days = (now - datetime.strptime(pub_str[:10], "%Y-%m-%d")).days
        except ValueError:
            age_days = 9999

        papers.append({
            "id": arxiv_id,
            "title": title,
            "summary": summary[:300],
            "age_days": age_days,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        })

    return json.dumps(papers, default=str)


# ── Tool 2 — Fetch PDF text ────────────────────────────────────────────────────

@tool
def fetch_paper_text(pdf_url: str, title: str) -> str:
    """
    Download an arXiv PDF and extract its full text (first 4000 chars).
    Call this for each paper you want to read before indexing.
    Inputs: pdf_url (string), title (string).
    """
    try:
        resp = requests.get(
            pdf_url,
            headers={"User-Agent": "ResearchAgent/1.0"},
            timeout=30,
        )
        resp.raise_for_status()
        reader = PdfReader(io.BytesIO(resp.content))
        text = "\n\n".join(p.extract_text() or "" for p in reader.pages).strip()
        status = "ok" if text else "empty_pdf"
        return json.dumps({"title": title, "text": text[:4000], "status": status})
    except Exception as e:
        return json.dumps({"title": title, "text": "", "status": f"error: {e}"})


# ── Tool 3 — Index papers into FAISS ──────────────────────────────────────────

@tool
def index_papers(texts: list[str], titles: list[str]) -> str:
    """
    Chunk and embed paper texts into an in-memory FAISS vector store.
    Call this ONCE after fetching all paper texts, passing all texts and titles together.
    Inputs: texts (list of extracted text strings), titles (matching list of paper titles).
    """
    global _faiss_store
    _faiss_store = None

    all_docs: list[Document] = []
    for text, title in zip(texts, titles):
        if not text or not text.strip():
            continue
        docs = splitter.create_documents(
            texts=[text],
            metadatas=[{"title": title}],
        )
        all_docs.extend([d for d in docs if len(d.page_content.strip()) > 50])

    if not all_docs:
        return "No content to index — all texts were empty."

    _faiss_store = FAISS.from_documents(all_docs, embeddings_model)
    return f"Indexed {_faiss_store.index.ntotal} chunks from {len(texts)} paper(s)."


# ── Tool 4 — Semantic search ───────────────────────────────────────────────────

@tool
def semantic_search(query: str) -> str:
    """
    Search the FAISS vector store for chunks most relevant to the query.
    You MUST call index_papers before this tool. Returns excerpts with source titles.
    """
    if _faiss_store is None:
        return "Vector store is empty — call index_papers first."

    results = _faiss_store.similarity_search_with_score(query, k=top_k_chunks)
    if not results:
        return "No relevant chunks found."

    return "\n\n---\n\n".join(
        f"[{doc.metadata.get('title', 'Unknown')}] score={score:.3f}\n{doc.page_content[:500]}"
        for doc, score in results
    )


# ── Tool 5 — Synthesize summary ────────────────────────────────────────────────

@tool
def synthesize_summary(context: str, original_query: str) -> str:
    """
    Synthesize retrieved paper excerpts into a structured research summary.
    Call this LAST, after semantic_search has returned relevant context.
    Inputs: context (excerpts from semantic_search), original_query (user's question).
    """
    chain = (
        ChatPromptTemplate.from_messages([
            ("system", "You are an expert research synthesizer. Be accurate and cite paper titles."),
            ("human", """The user asked: "{original_query}"

Write a structured synthesis using these excerpts:

📌 Topic: {original_query}

🧾 Key Insights:
- (3-5 key findings)

📚 Top Contributions:
- (What each paper contributes — use exact paper titles)

🔍 Trends:
- (Emerging patterns)

⚠️ Challenges:
- (Open problems)

🧠 Simple Explanation:
(2-3 sentences for a non-technical reader)

---
{context}"""),
        ])
        | llm
        | StrOutputParser()
    )
    return chain.invoke({"original_query": original_query, "context": context})


# ── System prompt (replaces PromptTemplate — create_agent takes a plain string) ─

def _build_system_prompt(depth: str, sources: str, top_k: int) -> str:
    return f"""You are a Research Paper Intelligence Agent.

Research settings for this request:
- Depth: {depth}  (Quick = 1 search + 1 paper | Standard = 2 searches + 2 papers | Deep = 3 searches + 3 papers)
- Sources: {sources}
- Papers to fetch: {top_k}

Follow these steps in order:
1. Call search_arxiv {("once" if depth == "Quick" else "2 times" if depth == "Standard" else "3 times")}, using a different query angle each time.
2. Pick the {top_k} most relevant and recent papers. Call fetch_paper_text for each one.
3. Call index_papers ONCE, passing all fetched texts and titles together.
4. Call semantic_search to retrieve the most relevant excerpts.
5. Call synthesize_summary with the excerpts and the user's original question.

Never skip a step. Never call semantic_search before index_papers."""


# ── History helpers ────────────────────────────────────────────────────────────

def get_raw_history(session_id: str) -> list[dict]:
    return _raw_history.get(session_id, [])


def clear_session(session_id: str):
    _raw_history.pop(session_id, None)
    # MemorySaver sessions are isolated by thread_id; clearing raw history is enough for demo


# ── Run agent ──────────────────────────────────────────────────────────────────

TOOLS = [search_arxiv, fetch_paper_text, index_papers, semantic_search, synthesize_summary]


def run_research_agent(
    query: str,
    session_id: str,
    depth: str = "Standard",
    sources: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    Runs the agent for a given query and session.
    Returns (final_answer, readable_steps_list).
    """
    depth_to_top_k = {"Quick": 1, "Standard": 2, "Deep": 3}
    top_k = depth_to_top_k.get(depth, top_k_papers)
    sources_str = ", ".join(sources) if sources else "ArXiv"

    system_prompt = _build_system_prompt(depth, sources_str, top_k)

    # create_agent is the correct call in langchain 1.x
    # checkpointer + thread_id gives per-session conversation memory
    agent = create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
        checkpointer=_checkpointer,
    )

    config_dict = {"configurable": {"thread_id": session_id}}

    # stream() yields state snapshots; we collect all messages from the last one
    steps: list[str] = []
    final_answer = "Agent did not produce a final answer."

    for chunk in agent.stream(
        {"messages": [HumanMessage(content=query)]},
        config_dict,
        stream_mode="values",
    ):
        messages = chunk.get("messages", [])
        for msg in messages:
            # Tool call messages
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    arg_preview = str(tc.get("args", {}))[:80]
                    steps.append(f"🔧 **{tc['name']}** — `{arg_preview}…`")
            # Tool result messages
            if msg.__class__.__name__ == "ToolMessage":
                steps.append(f"   ↳ {str(msg.content)[:120]}…")
            # Final AI response (no tool calls = final answer)
            if msg.__class__.__name__ == "AIMessage" and not getattr(msg, "tool_calls", []):
                if msg.content:
                    final_answer = msg.content

    _raw_history[session_id].append({
        "query": query,
        "response": final_answer,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return final_answer, steps
