import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# --------------------------------------------------
# Configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_CLEAN = PROJECT_ROOT / "data" / "cleaned_decls.json"
FAISS_INDEX_PATH = PROJECT_ROOT / "data" / "faiss.index"
MODEL_NAME = "all-MiniLM-L6-v2"

COMMON_TYPES = {
    'nat': ['ℕ', 'Nat', 'natural number', 'natural numbers', 'counting number', 'counting numbers', 'nonnegative integer', 'non-negative integer', 'whole number', 'whole numbers'],
    'int': ['ℤ', 'Int', 'integer', 'integers', 'signed integer', 'signed integers'],
    'real': ['ℝ', 'Real', 'real number', 'real numbers', 'real analysis'],
    'rat': ['ℚ', 'Rat', 'rational number', 'rational numbers'],
    'complex': ['ℂ', 'Complex', 'complex number', 'complex numbers'],
    'list': ['List', 'Array', 'Finset', 'list', 'lists', 'sequence', 'sequences', 'array', 'arrays'],
    'set': ['Set', 'Fintype', 'set', 'sets', 'finite set', 'finite sets'],
    'group': ['Group', 'AbelianGroup', 'Subgroup', 'Morphism', 'group', 'groups', 'abelian group', 'abelian groups'],
    'ring': ['Ring', 'CommRing', 'Ideal', 'ring', 'rings', 'commutative ring', 'commutative rings'],
    'field': ['Field', 'SortedField', 'field', 'fields', 'field theory'],
    'monoid': ['Monoid', 'CommMonoid', 'monoid', 'monoids'],
    'vector': ['VectorSpace', 'Module', 'vector space', 'vector spaces', 'linear algebra'],
    'continuous': ['Continuous', 'ContinuousOn', 'ContinuousAt', 'continuous', 'continuity', 'continuous function', 'continuous functions'],
    'differentiable': ['Differentiable', 'Deriv', 'differentiable', 'differentiation', 'derivative', 'derivatives'],
    'metric': ['Metric', 'dist', 'norm', 'metric space', 'metric spaces', 'distance', 'normed space'],
    'topology': ['Topology', 'Open', 'Closed', 'topology', 'topological space', 'open set', 'closed set'],
}

def extract_type_keywords(text):
    text_lower = text.lower()
    matched_types = set()
    for category, type_variants in COMMON_TYPES.items():
        for variant in type_variants:
            if variant.lower() in text_lower:
                matched_types.add(category)
                break
    return matched_types

def compute_type_score(query_types, lemma_types):
    if not query_types: return 0.0
    matches = len(query_types & lemma_types)
    return min(matches / len(query_types), 1.0) if query_types else 0.0

# --------------------------------------------------
# Initialization & Pipeline
# --------------------------------------------------
try:
    print("Loading search pipeline...")
    model = SentenceTransformer(MODEL_NAME)
    
    with open(OUTPUT_CLEAN, encoding="utf-8") as f:
        decls = json.load(f)
        
    faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
    
    corpus = [f"{decl['name']} {decl['type']}".lower().split() for decl in decls]
    bm25 = BM25Okapi(corpus)
    
    decl_types = [extract_type_keywords(decl["type"]) for decl in decls]
    
except FileNotFoundError as e:
    raise RuntimeError(f"Missing index files. Please run 'run_index.py' first.\nError: {e}")

# --------------------------------------------------
# Hybrid Search Engine
# --------------------------------------------------
def search(query, top_k=5, hybrid_weight=0.7, type_weight=0.15):
    try:
        query_types = extract_type_keywords(query)
        
        q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype('float32')
        faiss_scores, faiss_indices = faiss_index.search(q_emb, len(decls))
        
        semantic_scores = np.zeros(len(decls), dtype=np.float32)
        semantic_scores[faiss_indices[0]] = faiss_scores[0]
        
        if semantic_scores.max() > semantic_scores.min():
            semantic_scores = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min())
        else:
            semantic_scores = np.zeros_like(semantic_scores)
            
        query_tokens = query.lower().split()
        bm25_scores = np.array(bm25.get_scores(query_tokens))
        
        if bm25_scores.max() > bm25_scores.min():
            bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min())
        else:
            bm25_scores = np.zeros_like(bm25_scores)
            
        type_scores = np.array([compute_type_score(query_types, lemma_types) for lemma_types in decl_types])
        
        bm25_weight = 1.0 - hybrid_weight - type_weight
        final_scores = (hybrid_weight * semantic_scores + 
                        bm25_weight * bm25_scores + 
                        type_weight * type_scores)
                        
        idxs = np.argsort(-final_scores)[:top_k]
        return [(decls[i]["name"], decls[i]["type"]) for i in idxs]
        
    except Exception as e:
        raise RuntimeError(f"Search failed: {e}")

if __name__ == "__main__":
    test_queries = [
        # =========================
        # EASY (direct keyword match)
        # =========================
        ("algebra_easy", "abelian groups"),
        ("analysis_easy", "continuous functions"),
        ("topology_easy", "open sets in topology"),
        ("nat_easy", "natural number induction"),
        ("linear_algebra_easy", "vector spaces"),

        # =========================
        # MEDIUM (multi-concept, standard math phrasing)
        # =========================
        ("algebra_medium", "subgroups of integers and group homomorphisms"),
        ("analysis_medium", "continuous and differentiable functions on real numbers"),
        ("ring_medium", "commutative rings with ideals and ring homomorphisms"),
        ("topology_medium", "closed sets and topological spaces"),
        ("linear_algebra_medium", "linear transformations between vector spaces over real numbers"),

        # =========================
        # HARD (multi-domain + abstraction)
        # =========================
        ("algebra_hard", "abelian groups and quotient structures of integers"),
        ("analysis_hard", "uniform continuity and convergence of functions on metric spaces"),
        ("linear_algebra_hard", "structure preserving maps between vector spaces"),
        ("topology_hard", "continuity and compactness in topological spaces"),
        ("nat_hard", "recursive definitions over natural numbers and induction principles"),

        # =========================
        # VERY HARD (hybrid reasoning)
        # =========================
        ("hybrid_hard", "continuous group actions on metric spaces over ℝ"),
        ("hybrid_hard2", "functions preserving algebraic structure between rings and fields"),
        ("hybrid_hard3", "interaction between topology and algebraic structures in vector spaces"),

        # =========================
        # ADVERSARIAL / FUZZY (tests robustness)
        # =========================
        ("fuzzy_semantic", "structures that preserve operations between mathematical objects"),
        ("fuzzy_keyword", "rings groups fields ideals modules"),
        ("fuzzy_natural_language", "how functions behave when they don't break structure"),
    ]

    for label, query in test_queries:
        print(f"\n{'='*70}")
        print(f"[{label.upper()}] Query: {query}")
        print('='*70)

        results = search(query, top_k=5)

        for i, (name, typ) in enumerate(results, 1):
            print(f"{i}. {name}")
            print(f"   Type: {typ[:120]}..." if len(typ) > 120 else f"   Type: {typ}")
            print()