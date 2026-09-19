"""A finite regression gate, not a general reliability or safety score."""
import argparse
import json
from pathlib import Path
from app.chain import Assistant

ROOT = Path(__file__).resolve().parents[1]

def evaluate(assistant, cases):
    rows = []
    for case in cases:
        try:
            answer = assistant.invoke(case["question"])
            checks = {
                "status": answer.status == case["status"],
                "citations": [s.id for s in answer.sources] == case["source_ids"],
                "facts": all(t.lower() in answer.answer.lower() for t in case["required"]),
                "grounding": answer.status == "refused" or all(
                    answer.answer == s.excerpt for s in answer.sources),
            }
            # Exact extractive grounding is the demo contract. For a real model, this
            # is a deliberately strict proxy that will reject valid paraphrases too.
            rows.append({"id": case["id"], "passed": all(checks.values()),
                         "checks": checks, "response": answer.model_dump()})
        except Exception as exc:
            rows.append({"id": case["id"], "passed": False, "error": type(exc).__name__})
    return {"mode": assistant.mode, "total": len(rows),
            "passed": sum(r["passed"] for r in rows), "cases": rows}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "openai"], default="demo")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/golden.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/latest.json")
    args = parser.parse_args()
    report = evaluate(Assistant(args.mode), json.loads(args.dataset.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']}/{report['total']} cases passed ({args.mode}); {args.output}")
    raise SystemExit(0 if report["total"] > 0 and report["passed"] == report["total"] else 1)

if __name__ == "__main__":
    main()
