# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-06-13

### Added
- **Native FAISS Serialization:** Added direct integration of `faiss.IndexFlatIP` to the build pipeline to pre-compile and write high-density vector states to a binary `faiss.index` file.
- **Search Pipeline Unit Tests:** Added explicit test blocks (`test_extract_type_keywords` and `test_compute_type_score`) to validate Unicode character translation mapping and relative alignment math.

### Changed
- **Repository Directory Restructuring:** Reorganized layout by introducing dedicated root-level folders (`scripts/` and `tests/`) to cleanly segregate execution workflows and validation code from core engine utilities.
- **Pipeline Execution Renaming:** Relocated and renamed `python/index.py` to `scripts/run_index.py` to establish it explicitly as an asynchronous pipeline builder task.
- **Test Suite Migration:** Relocated and split test files into the `tests/` directory; renamed the core test runner to `test_pipeline.py` and updated path insertion hooks to dynamically track modules across both `python/` and `scripts/`.
- **API Target Testing:** Moved `test_api.py` to `tests/test_api.py` and refactored path resolution logic to smoothly map back into `python/api.py` without loading heavy global ML models.
- **Decoupled Search Architecture:** Completely stripped compilation tasks out of `search.py`. The engine now initializes instantly at runtime by loading pre-built binaries via `faiss.read_index`.
- **FAISS Vector Scanning:** Swapped pure NumPy matrix dot-products (`embeddings @ q_emb`) out for highly optimized, C++ multithreaded FAISS index lookup scans.
- **Positional Array Reconstruction:** Implemented a score alignment layer in the search sequence to map sorted FAISS results back to original absolute coordinates, maintaining precise alignment with global BM25 and type heuristic data structures.

### Improved
- Expanded `COMMON_TYPES` with additional natural language aliases for all type categories (numeric types, collections, algebraic structures, analysis/topology) to improve type-aware search recall.
- Enhanced test queries in `search.py` with categorized examples covering algebra, analysis, linear algebra, foundations, topology, and hybrid cases for better evaluation.
- Updated API example query to demonstrate more comprehensive search capabilities.

### Technical
- Forced explicit `float32` compliance on array vector sets during indexing to fulfill native FAISS memory-mapped alignment bounds.

## [1.1.0] - 2026-06-06

### Added
- Hybrid BM25 keyword search (rank-bm25 library) blended with semantic embeddings.
- Type-aware ranking using mathematical type categories (Nat, Int, Real, List, Set, Group, Ring, Field, Continuous, Topology, etc.).
- Pre-computed type categories for efficient search (eliminates per-query type extraction overhead).
- Configurable weight parameters for semantic/keyword/type ranking.

### Improved
- Search relevance on keyword-heavy queries like "list operations" and "natural number induction".
- Query latency for large corpus (20K+ declarations) via initialization-time pre-computation.
- Type matching now distinguishes foundational lemmas (e.g., `Nat.gcd induction` vs. proof internals).

### Technical
- BM25 scoring normalized to [0, 1] range.
- Weights: 70% semantic + 15% BM25 keyword + 15% type matching (tunable).
- Type categories pre-computed from all 20K+ declarations at module load time.

## [1.0.0] - 2026-06-05

### Added
- Core RAG pipeline for Lean4 mathlib semantic search.
- Lean4 exporter (`lean_export/Dump.lean`) to extract lemma/theorem declarations.
- Python indexing pipeline (`python/index.py`) with declaration cleaning and normalization.
- Semantic search via sentence-transformers embeddings (`python/search.py`).
- FastAPI REST endpoint for queries (`python/api.py`).
- Support for cosine similarity ranking on normalized embeddings.
- Pre-generated embeddings and cleaned declarations for mathlib.

### Changed
- Fixed query embedding normalization in search to use proper cosine similarity.

### Notes
- Large data artifacts: ~200 MB JSON + ~430 MB embeddings.
- Requires Lean4 toolchain and Python 3.10+ for full setup.