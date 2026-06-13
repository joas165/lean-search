import json
import re
import os
import numpy as np
import faiss
from pathlib import Path
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# Configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = Path(__file__).parent.parent

# Read the raw data directly from where Lean exports it
INPUT_JSON = PROJECT_ROOT / "lean_export" / "data" / "decls.json"

# Save your ML outputs into your main data folder
OUTPUT_EMB = PROJECT_ROOT / "data" / "embeddings.npy"
OUTPUT_CLEAN = PROJECT_ROOT / "data" / "cleaned_decls.json"
OUTPUT_FAISS = PROJECT_ROOT / "data" / "faiss.index"

MODEL_NAME = "all-MiniLM-L6-v2"

# Regex Cleaners
UNIVERSE_RE = re.compile(r"Type u(_\d+)?")
INST_RE = re.compile(r"\[inst[^]]*\]")
PROOF_RE = re.compile(r"\._proof.*$")
PRIVATE_PREFIX_RE = re.compile(r"^_private\.")
WHITESPACE_RE = re.compile(r"\s+")

DROP_NAME_PATTERNS = [r"\._proof", r"\._simp", r"\._match", r"\.rec$", r"\.casesOn$", r"\.wf$"]
DROP_PREFIXES = ["_private."]
DROP_MODULES = ["[anonymous]"]

def should_keep_decl(decl: dict) -> bool:
    name = decl["name"]
    module = decl.get("module", "")
    if module in DROP_MODULES: return False
    for p in DROP_PREFIXES:
        if name.startswith(p): return False
    for pat in DROP_NAME_PATTERNS:
        if re.search(pat, name): return False
    if len(decl["type"]) < 20: return False
    return True

def clean_type(t: str) -> str:
    t = UNIVERSE_RE.sub("Type", t)
    t = INST_RE.sub("", t)
    t = t.replace("∀", "for all").replace("→", "->").replace("↔", "<->")
    t = re.sub(r"\bEq\b", "equals", t)
    return WHITESPACE_RE.sub(" ", t).strip()

def clean_name(name: str) -> str:
    name = PRIVATE_PREFIX_RE.sub("", name)
    name = PROOF_RE.sub("", name)
    return name.replace(".", " ").strip()

def infer_kind(name: str) -> str:
    lname = name.lower()
    if "theorem" in lname: return "theorem"
    if "lemma" in lname: return "lemma"
    if "instance" in lname or lname.startswith("inst"): return "instance"
    if "def" in lname: return "definition"
    return "declaration"

def infer_domain(module: str) -> str:
    return module.split(".")[0] if module else "general"

def build_embedding_text(name: str, typ: str, module: str) -> str:
    return f"{infer_kind(name)} {name}. domain {infer_domain(module)}. statement {typ}"

def main():
    os.makedirs(PROJECT_ROOT / "data", exist_ok=True)
    
    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading declarations...")
    with open(INPUT_JSON, encoding="utf-8") as f:
        decls = json.load(f)

    cleaned_decls = []
    texts = []

    print("Cleaning declarations...")
    for d in tqdm(decls):
        if not should_keep_decl(d):
            continue

        name = clean_name(d["name"])
        typ = clean_type(d["type"])
        module = d.get("module", "")
        text = build_embedding_text(name, typ, module)

        cleaned_decls.append({
            "module": module,
            "domain": infer_domain(module),
            "kind": infer_kind(name),
            "name": name,
            "type": typ,
            "embedding_text": text,
        })
        texts.append(text)

    print("Encoding embeddings...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype('float32')

    print("Saving NumPy array...")
    np.save(OUTPUT_EMB, embeddings)

    with open(OUTPUT_CLEAN, "w", encoding="utf-8") as f:
        json.dump(cleaned_decls, f, ensure_ascii=False)

    print("Building and saving native FAISS index...")
    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(dimension)
    faiss_index.add(embeddings)
    faiss.write_index(faiss_index, str(OUTPUT_FAISS))

    print("Done!")

if __name__ == "__main__":
    main()