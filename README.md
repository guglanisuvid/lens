# Lens

> Point it at your documents. Ask it anything.

Task-based document intelligence from the CLI. Upload PDFs, run tasks, get structured answers with citations.

## Setup

```bash
git clone https://github.com/yourusername/lens.git
cd lens
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

## Usage

```bash
# Index documents
python main.py upload contracts/

# Run a task across all indexed docs
python main.py task "Compare payment terms and SLA across all vendors"

# Ask a question
python main.py ask "What is the liability cap for Vendor B?"

# List indexed documents
python main.py list

# Clear the index
python main.py clear
```
