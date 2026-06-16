Markdown
# Lean Mathlib RAG Search

This project builds a Hybrid Retrieval-Augmented Generation (RAG) system for the Lean 4 Mathlib library. It extracts lemma and theorem declarations from Mathlib, converts them into JSON, and enables fast semantic and structural search by combining dense vector embeddings with common type-signature filtering.

The goal is to quickly find existing lemmas or theorems in Mathlib that are relevant to a natural language query or a specific type pattern.

---

## Why Hybrid Semantic & Structural Search for Mathlib?

Mathlib is one of the largest formal math libraries, containing **thousands of lemmas and theorems**. Traditional keyword search fails here, and raw semantic search alone can sometimes overlook exact structural requirements:

- **Semantic density** — Each declaration carries enormous semantic weight through its type signature, which encodes relationships to other declarations, axioms, and type classes.
- **Common Type Intersections** — Many theorems share underlying structural types (e.g., operations on `OrderedCommRing`, `MetricSpace`, or basic mappings over `ℕ`). A hybrid approach matches the *informal intent* via embeddings and ranks/filters results based on shared, common type dependencies.
- **Naming variance** — Lemmas are named by convention but not uniformly. A theorem about commutativity might be `add_comm`, `comm_add`, or something entirely different.
- **High dimensionality** — A single query can have dozens of relevant lemmas. Finding the *best* matches requires ranking by conceptual similarity, not just string matching.

**Our hybrid strategy solves this** by using FAISS for dense vector search to capture informal mathematical intuition, paired with a matching layer that scores declarations sharing common type definitions and algebraic structures.

---

## Overview

The project consists of two core parts:

### 1. Lean 4 Exporter
* Loads Mathlib.
* Extracts lemmas, theorems, and their full type signatures from the environment.
* Dumps the raw declarations into a JSON file.

### 2. Python Hybrid RAG Pipeline
* Filters and normalizes mathematical definitions.
* Generates dense vector embeddings for semantic retrieval.
* Maps and indexes common types to allow structural intersection matching.
* Powers an optimized vector/type search via FAISS and an optional FastAPI REST service.

---

## Project Structure

lean-search/
│
├── lean_export/         # Lean 4 exporter
│   ├── Dump.lean
│   ├── lakefile.lean
│   ├── lean-toolchain
│   ├── lake-manifest.json
│   └── .lake/
│
├── python/              # Python RAG pipeline
│   ├── api.py
│   ├── embed.py
│   ├── search.py
│   └── run_index.py
│

├── data/                # Data artifacts (Git ignored except samples)
│   ├── cleaned_decls.json
│   ├── decls.json
│   ├── embeddings.npy
│   └── faiss.index
│
├── tests/               # Local test suites
│   ├── test_pipeline.py
│   └── test_api.py
│
├── requirements.txt
└── README.md


---

## Requirements

### Lean Side
* Lean 4
* Lake
* `elan` (Lean toolchain manager)

Install from: [https://lean-lang.org/install/](https://lean-lang.org/install/)

### Python Side
* Python 3.10+
* `pip`

---

## Setup

### 1. Build the Lean Exporter

From the project root:

```bash
cd lean_export
lake update
lake build Dump
lake env .\.lake\build\bin\Dump.exe
(On macOS/Linux, run ./.lake/build/bin/Dump in the last step)

This generates data/decls.json, containing raw Mathlib lemmas, names, and types.

Note: The generated data and embeddings are large. Expect about 200 MB for the JSON exports and 430 MB for the vector matrices. Ensure you have adequate disk space.

2. Install Python Dependencies
From the repository root, create and activate a virtual environment, then install requirements:

Bash
python -m venv venv
# Windows:
.\venv\Scripts\python.exe -m pip install -r requirements.txt
# macOS/Linux:
./venv/bin/python -m pip install -r requirements.txt
3. Parse Types and Generate the Hybrid Index
This step processes the raw export, indexes common type constraints, and writes the vector index:

Bash
python python/run_index.py
This creates:

data/cleaned_decls.json — Filtered declarations with normalized signatures.

data/embeddings.npy — Calculated vector representations.

data/faiss.index — The compiled FAISS index file for fast similarity lookup.

Running Search
Local CLI Search
After indexing, you can query the hybrid engine directly via the terminal:

Bash
python python/search.py
Example input: commutativity of addition

The search engine will utilize dense embeddings to find conceptual matches, and then leverage the common type definitions to score and surface the most structurally relevant Mathlib lemmas.

Web UI and REST API
To launch the FastAPI service interface locally:

Bash
# Windows
.\venv\Scripts\python.exe -m uvicorn api:app --app-dir python --reload
# macOS/Linux
./venv/bin/python -m uvicorn api:app --app-dir python --reload
Interactive Web Interface: Go to http://127.0.0.1:8000/

JSON API Endpoint: Query directly via http://127.0.0.1:8000/query?q=your+query+here

Testing
To verify the integration pipeline, structural type parsing, and response formatting, run the test suites locally:

Bash
python -m unittest tests/test_pipeline.py
python -m unittest tests/test_api.py
Note: Since the search pipeline depends heavily on heavy local binary index artifacts (faiss.index) and local environmental path configurations, testing should be performed locally within your virtual environment rather than through cloud CI automation hooks.


