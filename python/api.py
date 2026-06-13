from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from search import search

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="Lean RAG API",
    description="Semantic search for Lean4 mathlib declarations",
    version="1.0.0"
)

@app.get("/query/")
def query(q: str, k: int = 5):
    """
    Search for relevant lemmas/theorems in mathlib.
    
    Parameters:
    - q: Natural language query (e.g., "commutativity of addition")
    - k: Number of results to return (default 5)
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty")
    
    if k < 1 or k > 100:
        raise HTTPException(status_code=400, detail="Parameter 'k' must be between 1 and 100")
    
    try:
        results = search(q, top_k=k)
        return {"query": q, "results": [{"name": n, "type": t} for n, t in results]}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    q: str = "",
    k: int = Query(default=5, ge=1, le=25),
):
    """Render the search frontend."""
    results = []
    error = None
    query_text = q.strip()

    if query_text:
        try:
            results = [{"name": n, "type": t} for n, t in search(query_text, top_k=k)]
        except RuntimeError as e:
            error = str(e)
        except Exception as e:
            error = f"Search failed: {str(e)}"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "query": q,
            "k": k,
            "results": results,
            "error": error,
            "searched": bool(query_text),
        },
    )


@app.get("/api")
def api_info():
    """API info and usage."""
    return {
        "message": "Lean RAG API v1.0.0",
        "usage": "GET /query/?q=<query>&k=<num_results>",
        "example": "GET /query/?q=continuous+and+differentiable+functions+on+real+vector+spaces&k=5"
    }
