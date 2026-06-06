"""Task decomposition and answer synthesis — supports Groq, OpenAI, Anthropic, Ollama."""
import os
import json
from dotenv import load_dotenv
from lens.retriever import retrieve, retrieve_multi

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    if PROVIDER == "groq":
        from groq import Groq
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not set in .env")
        _client = Groq(api_key=key)

    elif PROVIDER == "openai":
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set in .env")
        _client = OpenAI(api_key=key)

    elif PROVIDER == "anthropic":
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set in .env")
        _client = anthropic.Anthropic(api_key=key)

    elif PROVIDER == "ollama":
        from openai import OpenAI
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        _client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{PROVIDER}'. Choose: groq, openai, anthropic, ollama")

    return _client


def _default_model() -> str:
    defaults = {
        "groq":      "llama-3.1-8b-instant",
        "openai":    "gpt-4o-mini",
        "anthropic": "claude-haiku-4-5-20251001",
        "ollama":    "llama3",
    }
    return os.getenv("LLM_MODEL", defaults.get(PROVIDER, ""))


def _chat(messages: list[dict], temperature: float = 0.1) -> str:
    client = _get_client()
    model  = _default_model()

    if PROVIDER == "anthropic":
        # Anthropic uses a different SDK interface
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_msgs  = [m for m in messages if m["role"] != "system"]
        kwargs = {"model": model, "max_tokens": 2048, "messages": user_msgs, "temperature": temperature}
        if system_msg:
            kwargs["system"] = system_msg
        response = client.messages.create(**kwargs)
        return response.content[0].text.strip()

    # Groq, OpenAI, Ollama all use OpenAI-compatible interface
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _decompose_task(description: str) -> list[str]:
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
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {chunk['source']}, Page {chunk['page']}\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def run_task(description: str) -> dict:
    queries = _decompose_task(description)
    chunks  = retrieve_multi(queries, n_per_query=4)
    if not chunks:
        return {"output": "No relevant documents found in the index.", "sources": []}

    context = _format_chunks(chunks)
    prompt  = f"""You are a document analyst. Using ONLY the provided document excerpts, complete the following task.

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
    output  = _chat([{"role": "user", "content": prompt}], temperature=0.0)
    sources = [{"source": c["source"], "page": c["page"], "score": c["score"]} for c in chunks]
    return {"output": output, "sources": sources}


def ask_question(question: str) -> dict:
    chunks = retrieve(question, n_results=5)
    if not chunks:
        return {"answer": "No relevant documents found in the index.", "sources": []}

    context = _format_chunks(chunks)
    prompt  = f"""Answer the following question using ONLY the provided document excerpts.

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
