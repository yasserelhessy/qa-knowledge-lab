import json
from pathlib import Path
from app.evaluate import evaluate
from app.models import Answer, Source

CASES = json.loads((Path(__file__).resolve().parents[1] / "data/golden.json").read_text())

def test_golden_regression(assistant):
    report = evaluate(assistant, CASES)
    assert report["total"] >= 12
    assert report["passed"] == report["total"], report


def test_gate_detects_unsupported_answer():
    class Hallucinating:
        mode = "demo"
        def invoke(self, question):
            return Answer(answer="Invented claim", status="answered", sources=[], mode="demo", retrieval_score=1)
    assert evaluate(Hallucinating(), CASES)["passed"] == 0


def test_gate_detects_wrong_fact_with_correct_citation():
    class WrongFact:
        mode = "demo"
        def invoke(self, question):
            return Answer(answer="API contract Playwright plus invented detail", status="answered",
                sources=[Source(id="release", title="Release gates", excerpt="API contract Playwright")],
                mode="demo", retrieval_score=1)
    row = evaluate(WrongFact(), [CASES[0]])["cases"][0]
    assert row["checks"]["facts"]
    assert not row["checks"]["grounding"]
    assert not row["passed"]
