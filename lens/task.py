"""Task decomposition and answer synthesis via Groq (llama3.1-8b-instant)."""
import os
import json
from groq import Groq
from dotenv import load_dotenv
from lens.retriever import retrieve, retrieve_multi

load_dotenv()

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        _client = Groq(api_key=api_key)
    return _client


def _chat(messages: list[dict], temperature: float = 0.1) -> str:
    response = get_client().chat.completions.create(
        model       = "llama-3.1-8b-instant",
        messages    = messages,
        temperature = temperature,
    )
    return response.choices[0].message.content.strip()


def _decompose_task(description: str) -> list[str]:
    """Ask the LLM to break a task into 3-5 search queries."""
    prompt = f"""You are a search query generator. Given a task, generate 3-5 specific search queries
to retrieve all relevant information needed to complete that task from a document database.

Task: {description}

Return ONLY a JSON array of query strings. No explanation. Example:
["query 1", "query 2", "query 3"]"""

    result = _chat([{"role": "user", "content": prompt}])
    try:
        queries = json.loads(result)
        return queries if isinstance(queries, list) else [description]
    except Exception:
        return [description]


def _format_chunks(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string with citations."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {chunk['source']}, Page {chunk['page']}\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def run_task(description: str) -> dict:
    """
    1. Decompose task into sub-queries
    2. Retrieve relevant chunks per sub-query
    3. Synthesize structured markdown table via Groq
    Returns: {output, sources}
    """
    # Step 1: decompose
    queries = _decompose_task(description)

    # Step 2: retrieve across all queries
    chunks = retrieve_multi(queries, n_per_query=4)
    if not chunks:
        return {"output": "No relevant documents found in the index.", "sources": []}

    context = _format_chunks(chunks)

    # Step 3: synthesize
    prompt = f"""You are a document analyst. Using ONLY the provided document excerpts, complete the following task.

Task: {description}

Document excerpts:
{context}

Instructions:
- Return a markdown table if comparison is needed
- Be concise and factual
- Only use information from the excerpts
- After the table/answer, list citations as: [n] filename, page X
- If information is missing, say "Not found in documents"
"""

    output = _chat([{"role": "user", "content": prompt}], temperature=0.0)
    sources = [{"source": c["source"], "page": c["page"], "score": c["score"]} for c in chunks]

    return {"output": output, "sources": sources}


def ask_question(question: str) -> dict:
    """
    Standard Q&A with citations.
    Returns: {answer, sources}
    """
    chunks = retrieve(question, n_results=5)
    if not chunks:
        return {"answer": "No relevant documents found in the index.", "sources": []}

    context = _format_chunks(chunks)

    prompt = f"""Answer the following question using ONLY the provided document excerpts.

Question: {question}

Document excerpts:
{context}

Instructions:
- Answer directly and concisely
- Cite your sources inline as [1], [2] etc.
- If the answer is not in the documents, say "This information was not found in your documents"
"""

    answer  = _chat([{"role": "user", "content": prompt}], temperature=0.0)
    sources = [{"source": c["source"], "page": c["page"], "score": c["score"]} for c in chunks]

    return {"answer": answer, "sources": sources}
