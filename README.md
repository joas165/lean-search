# Lean Mathlib RAG Search

This project builds a simple Retrieval-Augmented Generation (RAG) system for the Lean4 mathlib library.
It extracts lemma and theorem declarations from mathlib, converts them into JSON, and enables semantic search using embeddings.

The goal is to quickly find existing lemmas or theorems in mathlib that are relevant to a natural language query.

---

## Why Semantic Search for Mathlib?

Mathlib is one of the largest formal math libraries, with **thousands of lemmas and theorems**. Traditional keyword search fails here:

- **Semantic density** — Each declaration carries enormous semantic weight through its type signature, which encodes relationships to other declarations, axioms, and type classes.
- **Indirect relevance** — A query like *"prove properties of integer addition"* might match lemmas in unexpected modules (e.g., `Monoid.comm`, `Nat.add_assoc`) that keyword search would miss.
- **Naming variance** — Lemmas are named by convention but not uniformly. A theorem about commutativity might be `add_comm`, `comm_add`, or something entirely different.
- **High dimensionality** — A single query can have dozens of relevant lemmas. Finding the *best* matches requires ranking by conceptual similarity, not just string matching.

**Semantic embeddings solve this** by learning that mathematically similar statements should have similar representations, regardless of naming or surface syntax. This enables:

- Finding lemmas about `ℕ` that also apply to other additive structures
- Matching informal mathematical intuition to formal Lean code
- Discovering relevant auxiliary lemmas even when keyword search draws a blank

This approach is increasingly studied in formal math research (see papers on neural proof search and learning-assisted theorem proving on arXiv).

---

## Overview

The project consists of two parts:

### 1. Lean4 exporter

* Loads mathlib
* Extracts lemmas and theorems from the environment
* Dumps them into a JSON file

### 2. Python RAG pipeline

* Generates embeddings for declarations
* Performs semantic search
* Optional REST API for querying

---

## Project Structure

```
lean-rag/
│
├── lean_export/        # Lean4 exporter
│   ├── Dump.lean
│   ├── lakefile.lean
│   ├── lean-toolchain
│   ├── lake-manifest.json
│   └── .lake/
│
├── python/             # Python RAG pipeline
│   ├── api.py
│   ├── embed.py
│   ├── search.py
│   
├── data/
│   ├── cleaned_decls.json
│   ├── decls.json
│   |── embeddings.npy
│   |── faiss.index
|    
│
├── tests/
│   ├── test_api.json
│   ├── test_pipeline.json
│
├── scripts/
│   ├── run_index.py
│  
├── requirements.txt
└── README.md
```

---

## Requirements

### Lean side

* Lean4
* Lake
* elan (Lean toolchain manager)

Install from:

[https://lean-lang.org/install/](https://lean-lang.org/install/)

---

### Python side

* Python 3.10+
* pip

---

## Setup

### 1. Build the Lean exporter

From project root:

```bash
cd lean_export
lake update
lake build Dump
lake env .\.lake\build\bin\Dump.exe
```

This generates:

```
data/decls.json
```

containing mathlib lemmas and theorems.

> Note: the generated data and embeddings are large. Expect about 200 MB for the JSON exports and 430 MB for `data/embeddings.npy`, so ensure you have enough disk space and time for generation.

---

### 2. Install Python dependencies

From the repository root, create and use a virtual environment:

```bash
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux, use:

```bash
python -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

---

### 3. Clean declarations and generate embeddings

This step must be run before search. It:
- Loads the raw `data/decls.json` from the Lean exporter
- Filters out noise (private declarations, proof artifacts, etc.)
- Normalizes type strings
- Generates semantic embeddings

From the repository root:

```bash
python scripts/run_index.py
```

Or from the `python/` directory:

```bash
cd python
python run_index.py
```

This creates:
- `data/cleaned_decls.json` — filtered declarations
- `data/embeddings.npy` — semantic embeddings for search

---

### 4. Run search locally

After step 3 completes, run searches:

From the repository root:

```bash
python python/search.py
```

Or from the `python/` directory:

```bash
cd python
python search.py
```

Example query:

```
commutativity of addition
```

The script prints relevant mathlib lemmas.

---

### 5. (Optional) Run web app and REST API

After step 3 completes, start the FastAPI app from the repository root:

```bash
.\venv\Scripts\python.exe -m uvicorn api:app --app-dir python --reload
```

On macOS/Linux, use:

```bash
./venv/Scripts/python -m uvicorn api:app --app-dir python --reload
```

Then open the web interface:

```
http://127.0.0.1:8000/
```

The JSON API remains available at:

```
http://127.0.0.1:8000/query?q=commutativity+of+addition
```

---

## Testing

Lightweight tests are included for the core pipeline helpers and API endpoint functions:

```bash
.\venv\Scripts\python.exe python/tests.py
.\venv\Scripts\python.exe python/test_api.py
```

Tests cover:
- Module imports
- Type/name cleaning and normalization
- Declaration filtering
- Domain/kind inference
- API query validation and response formatting

---

## GitHub Actions (Continuous Integration)

Tests run automatically on every push to `main` and for pull requests:

- Runs on Python 3.10 and 3.11
- View results in the **Actions** tab on your GitHub repository
- Configuration: `.github/workflows/tests.yml`

---

## Notes

* The Lean project only exports data and has no dependency on Python.
* The Python side performs embedding and retrieval.
* The `lean-toolchain` file pins the Lean version for reproducible builds.
* No vector database is required for the basic version.
* Error handling ensures helpful messages if data files are missing or corrupt.


