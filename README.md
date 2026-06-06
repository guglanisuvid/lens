# Lens

> RAG, but you tell it what to *do* — not just what to ask.

Local document intelligence from the CLI. Upload PDFs, define a task, get structured answers with citations — across 140 files, nested folders, any path on your machine.

Built in 1 day. Yes, 1 day. The kind of thing consultants charge $50,000 to "architect" and "deliver in Q3."

---

## What It Does

Everyone has seen "chat with your PDF." You upload a doc, ask a question, get an answer. Useful. Boring. Done to death.

**Lens is different.** Instead of asking questions, you define a *task*:

```
lens> /task compare admission requirements across all university applications
lens> /task summarize rejection reasons from all rejection letters
lens> /task list all payment deadlines across these contracts
```

Lens decomposes your task into multiple search queries, retrieves the most relevant chunks from across all your documents simultaneously, deduplicates and ranks them by relevance, then synthesizes structured markdown output — tables, comparisons, summaries — with cited sources.

It also does regular Q&A if that's what you need.

And the whole thing runs in a persistent `lens>` shell. No browser. No cloud. No subscription. Just your terminal.

---

## How It Works

```
Your question or task
        │
        ▼
  Task Decomposition          ← LLM breaks task into 3–5 sub-queries
        │
        ▼
  Multi-Query Retrieval       ← Each query → embed → cosine search in LanceDB
        │
        ▼
  Deduplication + Ranking     ← Merge results, remove duplicates, sort by score
        │
        ▼
  LLM Synthesis               ← Answer with inline citations + conflict detection
        │
        ▼
  Rich Terminal Output        ← Markdown table, sources, relevance labels, excerpts
```

**Embeddings are 100% local** via Ollama's `nomic-embed-text` model — your documents never leave your machine during indexing. Only the retrieved text chunks (not full documents) are sent to the LLM API for answering.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Embeddings | Ollama + `nomic-embed-text` | Free, local, 768-dim vectors, no API key needed |
| Vector DB | LanceDB | Pure Python, no C++ build tools, persistent on disk |
| PDF parsing | PyMuPDF | Fast, prebuilt wheels, accurate page extraction |
| LLM | Groq / OpenAI / Anthropic / Ollama | Pluggable — swap with one env var |
| CLI | Custom REPL + Rich | Persistent shell with beautiful terminal output |
| Storage | `~/.lens/lancedb` | Your data stays on your machine |

---

## Setup — Exact Steps

### Step 1 — Install Python

Download and install Python 3.11 or later from [python.org](https://www.python.org/downloads/).

During installation on Windows, check **"Add Python to PATH"**.

Verify:
```bash
python --version
# Should print: Python 3.11.x or higher
```

### Step 2 — Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com).

After installation, open a terminal and start it:
```bash
ollama serve
```

Leave this terminal open — Ollama needs to stay running while you use Lens.

Pull the embedding model (one-time, ~270MB):
```bash
ollama pull nomic-embed-text
```

Verify it worked:
```bash
ollama list
# Should show: nomic-embed-text
```

### Step 3 — Clone and Install Lens

Open a new terminal (keep the Ollama one running):

```bash
git clone https://github.com/guglanisuvid/lens.git
cd lens
pip install -r requirements.txt
```

### Step 4 — Get a Free Groq API Key

Groq is the default LLM provider — it's free.

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up and create an API key
3. Copy the key (starts with `gsk_...`)

### Step 5 — Configure

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 6 — Run

```bash
python main.py
```

You'll see the `lens>` shell. You're ready.

### Step 7 — Index your first document

```
lens> /upload /path/to/your/documents
```

Then ask:

```
lens> /ask what is this document about?
```

---

## Commands

| Command | What it does |
|---|---|
| `/upload <path>` | Index a PDF/txt file or any folder (recursive — finds all nested files) |
| `/ask <question>` | Ask a question, get a cited answer |
| `/task <description>` | Run a structured task, get a markdown table |
| `/docs` | List all indexed documents grouped by folder |
| `/remove <name>` | Remove a single document from the index |
| `/clear` | Wipe the entire index |
| `/help` | Show all commands |
| `/exit` | Exit Lens |

No quotes needed. Everything after the command is your input:

```
lens> /ask what is the penalty for late payment in the vendor contracts
lens> /task compare all rejection letters and identify common reasons
lens> /upload D:\Documents\Contracts
```

---

## Multi-Provider LLM

Lens works with any major LLM provider. Set `LLM_PROVIDER` in `.env`:

### Groq (default — free tier, fast)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key
# Default model: llama-3.1-8b-instant
```

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
LLM_MODEL=gpt-4o-mini   # optional override
```

### Anthropic (Claude)
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
LLM_MODEL=claude-haiku-4-5-20251001   # optional override
```

### Ollama (fully local — zero API calls)
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```

With Ollama as both the embedding model and LLM, Lens runs **100% offline**. Nothing leaves your machine.

---

## What You See

```
lens> /ask which universities rejected my application?

Question: which universities rejected my application?

╭─────────────────────────── Answer ───────────────────────────────╮
│ Based on the rejection letters in your documents, the following   │
│ universities rejected your application: [1] THWS, [2] Bauhaus    │
│ Universität Weimar, [3] BTU Cottbus-Senftenberg, [4] Philipps    │
│ University Marburg, and [5] Universität Passau...                 │
╰───────────────────────────────────────────────────────────────────╯

  Sources

  Relevance   File                          Page
  ─────────────────────────────────────────────
  High        Rejection_THWS.pdf            1
  High        Rejection_BTU_Cottbus.pdf     1
  Med         Application_Form_Passau.pdf   3

  [1] ...We regret to inform you that your application for the Master...
  [2] ...After careful consideration, the admissions committee has...
  [3] ...Your application has been reviewed and unfortunately...
```

**Relevance labels** tell you how strongly each source matched your query — `High` (≥0.70), `Med` (≥0.50), `Low` (<0.50).

**Excerpts** show the exact text that was used to generate the answer — no more wondering what the model actually read.

**Conflict detection** — if two documents say different things, the answer starts with `⚠ Conflicting sources:` and explains the disagreement.

**Duplicate protection** — uploading the same folder twice skips already-indexed files automatically.

---

## Where Your Data Lives

```
~/.lens/lancedb        ← Vector index (persistent across sessions)
.env                   ← API keys (never committed)
```

The index survives restarts. Upload once, query forever (or until you `/clear`).

---

## Limitations

- Supports `.pdf` and `.txt` only (`.docx` coming eventually, maybe)
- LLM context window limits how many chunks can be synthesized at once
- Embeddings are character-based chunks — very short documents may not retrieve well
- The LLM can still hallucinate; always check the cited sources

---

## Built In 1 Day

One day. Not a weekend. Not a sprint. One day.

Apparently building a fully local RAG pipeline with multi-query decomposition, a persistent vector database, pluggable LLM providers, conflict detection, duplicate protection, and a beautiful CLI takes less time than most people spend in meetings arguing about what to build next quarter.

The irony is not lost on us.

---

## GitHub

[https://github.com/guglanisuvid/lens](https://github.com/guglanisuvid/lens)
