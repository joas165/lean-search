"""
Lightweight unit tests for the RAG pipeline helpers.

Run from the repository root with:
    python tests/test_pipeline.py
"""

from pathlib import Path
import sys

# Find the project root directory relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Point to both directories to handle split components
PYTHON_DIR = PROJECT_ROOT / "python"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_import_modules():
    """Verify helper modules can be imported without running the pipeline."""
    from run_index import clean_name, clean_type, infer_domain, infer_kind, should_keep_decl
    from search import extract_type_keywords, compute_type_score

    assert callable(clean_name)
    assert callable(clean_type)
    assert callable(infer_domain)
    assert callable(infer_kind)
    assert callable(should_keep_decl)
    assert callable(extract_type_keywords)
    assert callable(compute_type_score)


def test_clean_type():
    """Test type string normalization."""
    from run_index import clean_type

    result = clean_type("Type u_1 -> Type u_2")
    assert "u_1" not in result
    assert "u_2" not in result

    result = clean_type("Eq a b")
    assert "equals" in result.lower()

    result = clean_type("   Nat    ->    Nat  ")
    assert result == "Nat -> Nat"


def test_clean_name():
    """Test declaration name cleaning."""
    from run_index import clean_name

    assert clean_name("_private.Foo.bar") == "Foo bar"
    assert clean_name("List.map.rec") == "List map rec"
    assert clean_name("Nat.add._proof_1") == "Nat add"


def test_infer_kind():
    """Test declaration kind inference."""
    from run_index import infer_kind

    assert infer_kind("my_theorem") == "theorem"
    assert infer_kind("helper_lemma") == "lemma"
    assert infer_kind("Inst.something") == "instance"
    assert infer_kind("my_def") == "definition"
    assert infer_kind("Nat.add_comm") == "declaration"


def test_infer_domain():
    """Test domain extraction from module name."""
    from run_index import infer_domain

    assert infer_domain("Topology.ContinuousAt") == "Topology"
    assert infer_domain("Data.List.Basic") == "Data"
    assert infer_domain("") == "general"


def test_should_keep_decl():
    """Test declaration filtering logic."""
    from run_index import should_keep_decl

    assert should_keep_decl(
        {
            "name": "add_comm",
            "type": "forall a b : Nat, a + b = b + a",
            "module": "Data.Nat",
        }
    )

    assert not should_keep_decl(
        {
            "name": "_private.Foo.bar",
            "type": "forall a b : Nat, a + b = b + a",
            "module": "Data",
        }
    )

    assert not should_keep_decl(
        {
            "name": "foo",
            "type": "short",
            "module": "Data",
        }
    )

    assert not should_keep_decl(
        {
            "name": "something",
            "type": "forall a b : Nat, a + b = b + a",
            "module": "[anonymous]",
        }
    )


def test_extract_type_keywords():
    """Test mathematical category pattern matching on query/lemma texts."""
    from search import extract_type_keywords

    # Match raw unicode math notation
    assert "nat" in extract_type_keywords("forall (n : ℕ), n + 0 = n")
    assert "real" in extract_type_keywords("Continuous map over ℝ")
    
    # Match multi-word variations and complex contexts
    matches = extract_type_keywords("continuous functions on metric spaces")
    assert "continuous" in matches
    assert "metric" in matches


def test_compute_type_score():
    """Test type mathematical context weight scoring calculations."""
    from search import compute_type_score

    # Perfect intersection match
    assert compute_type_score({"nat"}, {"nat", "group"}) == 1.0
    
    # Half of the query constraints matched
    assert compute_type_score({"nat", "real"}, {"nat", "ring"}) == 0.5
    
    # Empty query fallback protection
    assert compute_type_score(set(), {"real"}) == 0.0


def run_all():
    tests = [
        test_import_modules,
        test_clean_type,
        test_clean_name,
        test_infer_kind,
        test_infer_domain,
        test_should_keep_decl,
        test_extract_type_keywords,
        test_compute_type_score,
    ]

    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    try:
        run_all()
    except Exception as exc:
        print(f"FAIL {exc}")
        sys.exit(1)