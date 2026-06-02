# CarnaticGPT 🎵🤖

CarnaticGPT is an advanced Retrieval-Augmented Generation (RAG) platform specialized in South Indian Carnatic Music. It leverages modern NLP processing, lightweight vector indices, a Python FastAPI back-end, and a premium Glassmorphic React dashboard to search, cite, analyze, and learn about Ragas, Composers, and classical music books.

---

## 🏛️ Project Architecture

```
CarnaticGPT/
├── backend/            # FastAPI REST backend & SQLite Auth/Telemetry DB
├── frontend/           # Premium glassmorphic React client built with Vite
├── scripts/            # Python automated RAG ingestion & data pipelines
├── data/               # Raw PDFs, extracted/cleaned texts, and FAISS database
├── models/             # Local embeddings or fine-tuned model configs
├── tests/              # Automated backend, frontend, and RAG pipelines tests
└── deployment/         # Docker Compose and Nginx production profiles
```

---

## ✨ Features

- **Rich Semantic Chat:** Chat naturally about ragas, composers, and classical texts. Supports high-fidelity citations.
- **Interactive Audio Player:** Live playback demo capability for Carnatic Ragas (e.g. Mayamalavagowla, Kalyani) directly from search citations.
- **Glassmorphic Dashboard:** Stunning real-time data visualizations of query volumes, feedback scores, and indexing status.
- **Structured RAG Pipeline:** Automated ingestion scripts: PDF parsing, OCR fallback, advanced text cleaning, token overlaps chunking, embedding generation, and FAISS indexing.
- **Secure Authentication & telemetry:** Login gating, secure user profiles, and chat logs history.

---

## 🚀 Quick Start

### 1. Ingestion Pipeline
To convert classical PDFs into the search index:
```bash
# Seed mock PDF/text data for instant verification
python scripts/generate_mock_data.py

# Ingest and clean documents
python scripts/extract_pdf.py
python scripts/clean_text.py
python scripts/chunk_text.py

# Create FAISS vector databases
python scripts/create_embeddings.py
```

### 2. Launch Backend Server
Ensure Python packages are installed:
```bash
pip install -r requirements.txt
uvicorn backend.server:app --reload --port 8000
```

### 3. Launch Frontend Client
Ensure Node dependencies are installed:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to explore CarnaticGPT!
