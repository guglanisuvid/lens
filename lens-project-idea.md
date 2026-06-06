# Lens — Task-Based Document Intelligence

> RAG, but you tell it what to do — not just what to ask.

---

## The Idea

Everyone knows you can chat with a PDF. That's been done to death — upload a document, ask questions, get answers. Useful, but limited.

**Lens** flips the model. Instead of asking questions, you define a *task* — and Lens runs it across all your documents and returns structured output. "Compare all vendor contracts." "Summarize rejection reasons from university applications." "Extract all deadlines across these PDFs." You get a markdown table, not a paragraph.

Under the hood it's RAG, but with multi-query decomposition: the task is broken into 3–5 sub-queries, each retrieves the most relevant chunks, the results are deduplicated and ranked by similarity, then an LLM synthesizes structured output from all of it.

The entire thing runs from a persistent interactive CLI — type `python main.py` and you get a `lens>` shell.

---

## The Problem

Knowledge workers spend hours manually searching through PDFs. Lawyers comparing contracts. Students tracking application statuses. Researchers cross-referencing papers. Analysts pulling data from reports.

The tools available are:
- **ChatGPT/Claude**: paste the document manually, lose context after the conversation ends, can't search across 50 files at once
- **NotebookLM**: browser-only, Google-dependent, not programmable
- **LangChain/LlamaIndex**: powerful but requires writing code to use
- **Enterprise RAG platforms**: $$$, require cloud upload, privacy concerns

Nothing that's local, free, private, and usable without writing code.

---

## Why CLI Over Web

- No server to run, no browser to open
- Works over SSH on a remote machine
- Pipe-friendly — scriptable for automation
- No auth, no accounts, no data leaving your machine (except the LLM call)
- Feels like a power tool, not a consumer product

---

## What Makes It Different

| Feature | Standard RAG chatbot | Lens |
|---|---|---|
| Interface | Ask questions | Define tasks |
| Output format | Free-form answer | Structured markdown table |
| Query strategy | Single embedding lookup | Multi-query decomposition |
| Scope | One document at a time | All indexed documents simultaneously |
| Storage | Session-only or cloud | Persistent local vector DB |
| Source citations | Sometimes | Always, with file + page |
| LLM provider | Fixed | Pluggable (Groq, OpenAI, Anthropic, Ollama) |
| Privacy | Cloud-dependent | Embeddings fully local via Ollama |

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.13 | Fast iteration, rich ML ecosystem |
| CLI/REPL | Custom `input()` loop + Rich | Persistent shell feel without a framework |
| PDF parsing | PyMuPDF (fitz) | Fast, accurate, prebuilt wheels for Python 3.13 |
| Embeddings | Ollama + nomic-embed-text | Free, local, 768-dim vectors, no API key |
| Vector DB | LanceDB | Pure Python, no C++ compilation, persistent on disk |
| LLM | Groq / OpenAI / Anthropic / Ollama | Pluggable via `LLM_PROVIDER` env var |
| Output | Rich panels + markdown tables | Clean terminal rendering |
| Storage | `~/.lens/lancedb` | Persistent across sessions, user-owned |

---

## Architecture

```
main.py                  Entry point — launches the REPL
  └── lens/
        ├── cli.py       Interactive REPL — /ask /task /upload /docs /clear /help /exit
        ├── parser.py    PDF + txt → overlapping text chunks (1000 chars, 200 overlap)
        ├── embedder.py  Ollama REST API → 768-dim vectors (nomic-embed-text)
        ├── indexer.py   LanceDB read/write — add_chunks, query, list_sources, clear
        ├── retriever.py retrieve(query) + retrieve_multi(queries) with deduplication
        ├── task.py      LLM client (multi-provider) — decompose + synthesize
        └── formatter.py Rich output — answer panels, source tables, folder tree
```

**RAG pipeline:**

```
/upload <path>
  └── parse_file()        Extract text by page
  └── chunk_text()        Split into overlapping chunks
  └── embed_chunks()      Ollama → vector per chunk
  └── add_chunks()        Store in LanceDB with source + page

/ask <question>
  └── embed_query()       Embed question → vector
  └── retrieve()          Cosine similarity → top 5 chunks
  └── ask_question()      LLM: answer with inline citations

/task <description>
  └── _decompose_task()   LLM: break into 3–5 sub-queries
  └── retrieve_multi()    Retrieve per query → deduplicate → rank
  └── run_task()          LLM: synthesize markdown table from all chunks
```

---

## Commands

```
lens> /upload <path>          Index a PDF/txt file or any folder (recursive)
lens> /ask <question>         Answer a question from your docs, with citations
lens> /task <description>     Run a structured task, get a markdown table
lens> /docs                   List all indexed documents grouped by folder
lens> /clear                  Wipe the entire index
lens> /help                   Show all commands
lens> /exit                   Exit Lens
```

---

## Multi-Query Decomposition

The key algorithmic insight: a task like *"compare admission requirements across all universities"* can't be answered by a single embedding lookup. The chunks that answer that question are spread across 15 different files.

The solution:
1. Ask the LLM to decompose the task into 3–5 focused search queries
2. Run each query independently against the vector DB
3. Deduplicate by content hash, rank by cosine similarity score
4. Feed the merged, ranked context to the LLM for synthesis

This retrieves far more relevant content than a single query while staying within the LLM's context window.

---

## Multi-Provider LLM

Lens is LLM-agnostic. Set `LLM_PROVIDER` in `.env` and optionally override the model:

```env
# Groq (default, free)
LLM_PROVIDER=groq
GROQ_API_KEY=your_key

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
LLM_MODEL=gpt-4o-mini

# Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
LLM_MODEL=claude-haiku-4-5-20251001

# Ollama (fully local, no API key)
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```

With Ollama for both embeddings and LLM, Lens runs 100% offline — no data leaves your machine.

---

## Step-by-Step Build Plan

### Phase 1 — Core RAG pipeline

**Step 1: Project scaffold**
```
lens/
  __init__.py, parser.py, embedder.py, indexer.py,
  retriever.py, task.py, formatter.py, cli.py
main.py, requirements.txt, .env.example
```

**Step 2: Parser**
- PyMuPDF for PDF page extraction
- 1000-char chunks with 200-char overlap
- Store `{text, page, source}` per chunk

**Step 3: Embedder**
- Ollama REST API call to `/api/embeddings`
- Warmup call on first use (cold model load)
- 120s timeout

**Step 4: LanceDB indexer**
- Persistent at `~/.lens/lancedb`
- Cosine metric for search
- `to_arrow()` instead of `to_pandas()` to avoid native lance dependency

**Step 5: Retriever**
- Single query: embed → cosine search → top N
- Multi-query: embed each → search each → deduplicate → sort by score

**Step 6: Task + ask**
- `ask_question`: single retrieve → LLM with citation prompt
- `run_task`: decompose → multi-retrieve → LLM with table synthesis prompt

### Phase 2 — CLI + polish

**Step 7: Interactive REPL**
- `lens>` prompt with `console.input()`
- Split on first whitespace — everything after the command is the argument (no quotes needed)
- `/help`, `/exit`, graceful `KeyboardInterrupt`

**Step 8: Rich output**
- Answer in a green panel with inline citations
- Task output as parsed markdown
- Sources table with score, file, page
- `/docs` grouped by folder with tree display

**Step 9: Multi-provider LLM**
- Factory function keyed by `LLM_PROVIDER`
- Groq/OpenAI/Ollama share the OpenAI-compatible SDK
- Anthropic uses its own SDK with system message extraction

---

## Features

### Shipped (v1.0)
- [x] PDF and .txt ingestion with overlapping chunking
- [x] Local embeddings via Ollama (nomic-embed-text)
- [x] Persistent vector index (LanceDB at `~/.lens/lancedb`)
- [x] `/ask` — Q&A with inline citations and source table
- [x] `/task` — multi-query decomposition + structured markdown output
- [x] `/upload` — recursive folder indexing (any path on the machine)
- [x] `/docs` — indexed file list grouped by folder
- [x] `/clear` — wipe index with confirmation
- [x] Multi-provider LLM (Groq, OpenAI, Anthropic, Ollama)
- [x] No-quotes REPL input — everything after command is the argument
- [x] Cosine similarity scoring (0–1 range)
- [x] Source citations with file path and page number
- [x] 100% local option (Ollama for both embeddings and LLM)

### Potential V2
- [ ] `/remove <file>` — delete a single document from the index
- [ ] `/export` — save task output to a markdown file
- [ ] Streaming LLM responses
- [ ] Web UI wrapper (FastAPI + simple HTML)
- [ ] `.docx` and `.md` support
- [ ] Re-index detection (skip already-indexed files)
- [ ] Named index profiles ("work", "personal", "research")
- [ ] Token usage display per query

---

## Real-World Use Cases Tested

| Task | Documents | Result |
|---|---|---|
| "Which universities rejected my application?" | 140 PDFs across nested folders | Named each university with rejection context |
| "What does this support doc cover?" | Chatbot support PDF | Summarized topic areas with page citations |

---

## Privacy Model

| Operation | Where it happens |
|---|---|
| Document parsing | Local |
| Embedding generation | Local (Ollama) |
| Vector storage | Local (`~/.lens/lancedb`) |
| LLM answer synthesis | Groq/OpenAI/Anthropic API (or local Ollama) |

Your documents never leave your machine. Only the retrieved text chunks (not the full documents) are sent to the LLM API. With Ollama as LLM provider, nothing is sent anywhere.

---

## Lessons Learned

**Python 3.13 + Windows package hell:** ChromaDB required C++ build tools to compile `chroma-hnswlib`. PyMuPDF 1.24 required Visual Studio. Solution: upgrade to PyMuPDF 1.25.5 (prebuilt wheels) and switch to LanceDB (pure Python). Always check for prebuilt wheels before assuming a package will install cleanly.

**Groq SDK version mismatch:** `groq==0.9.0` passed a `proxies` argument to `httpx`, which was removed in `httpx>=0.28`. Upgrading to `groq>=1.4.0` fixed it. SDK version pinning matters.

**LanceDB `to_pandas()` requires the native `lance` module:** The pure-Python LanceDB install doesn't bundle the native lance binary. Use `table.to_arrow().column("source").to_pylist()` instead.

**Cosine vs L2 distance:** LanceDB defaults to L2 (Euclidean) distance. `1 - L2_distance` produces negative scores for dissimilar vectors. Add `.metric("cosine")` to the search call.

**Ollama cold starts:** First embedding call times out at 30s while the model loads into memory. Fix: increase timeout to 120s and add a warmup call with a short string before processing real chunks.

---

## GitHub

[https://github.com/guglanisuvid/lens](https://github.com/guglanisuvid/lens)

---

*Built: June 2026 | Stack: Python, Ollama, LanceDB, Groq | Fully local embeddings, pluggable LLM*
