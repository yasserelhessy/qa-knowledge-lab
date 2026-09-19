"""Small, inspectable lexical retriever. No embeddings or network required."""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "knowledge.json"
STOP = set("a an the is are of to for do does how what when can i we our in on and should".split())

def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP

def load_documents(path: Path = DATA) -> list[dict]:
    return json.loads(path.read_text())

def retrieve(question: str, documents: list[dict]) -> dict:
    query = tokens(question)
    ranked = []
    for doc in documents:
        # Coverage penalizes unsupported extra concepts; threshold is deliberately simple.
        overlap = len(query & tokens(doc["keywords"]))
        score = overlap / max(len(query), 1)
        ranked.append((score, doc))
    score, best = max(ranked, key=lambda item: item[0], default=(0, None))
    return {"question": question, "document": best if score >= 0.6 else None,
            "score": round(score, 3)}
