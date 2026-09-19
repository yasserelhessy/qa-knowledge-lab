# Test strategy and release decision

## Scope

The system under test is the local assistant and its browser/API boundaries. The playbook describes a fictional order/payment system; this repository does not implement that payment API. Tests call the actual assistant API.

| Risk | Evidence | Boundary |
|---|---|---|
| Breaking client payloads | Independent `answer.schema.json` contract + HTTP tests | Snapshot deliberately must be reviewed when fields change |
| Invalid input reaches the chain | Missing, short, whitespace, oversized, wrong type, unknown-field, malformed-JSON tests | Not a full fuzzing suite |
| Unsupported questions get answers | Five negative golden cases + browser refusal | Vocabulary overlap may fool retrieval |
| Wrong facts or citations regress | Required substrings, exact source IDs, extractive evidence equality | Simple proxies; no semantic judge |
| Gate reports false success | Deliberately faulty assistants in evaluator tests | Checks known faults, not all possible defects |
| Test data leaks across tests | Fresh assistant/client fixture and injected synthetic corpus | No external datastore in this scope |
| Provider errors leak secrets | Fake failing provider, sanitized 502 response | No live-provider integration run |
| UI breaks important flows | Real-server Chromium tests for answer, evidence, refusal, recovery | No cross-browser matrix yet |
| Untrusted model text becomes HTML | Browser verifies text rendering of an HTML-like answer | Not a complete browser security assessment |
| Optional model wiring is wrong | Fake runnable checks prompt, parser, refusal and model bypass | Does not establish model quality |

## Gate

1. All non-browser tests pass.
2. All golden cases pass, including refusals.
3. All selected Chromium workflows pass against demo mode.
4. Inspect failures and reports; never update expected outcomes simply to make CI green.

GitHub Actions installs pinned dependencies, launches the real app, waits for readiness, and uploads reports/traces even on failure. It has a ten-minute timeout and never requires model credentials. CI has been authored but must run in Yasser's own GitHub repository before claiming a remote passing build.

## Dataset governance

`data/knowledge.json` contains six synthetic source records with stable IDs, titles, evidence text, and searchable keywords. `data/golden.json` contains seven supported and five unsupported cases. Every case has a unique ID, question, expected status, exact source IDs and required answer fragments. Review both files together for intentional contract changes. Add new cases before changing retrieval to preserve reproducible failures.

The dataset is small and co-designed with the retriever. A useful next increment is a held-out collection written by someone who has not seen its keyword rules, including ambiguous questions, paraphrases, mixed supported/unsupported requests, and adversarial instructions.

## Interpretation

The demo's exact evidence equality check measures an extractive contract. Required substrings alone are not truth checking. The strict equality check can reject correct real-model paraphrases and cannot establish general safety. Real-model evaluation needs separate criteria, repeated runs, a model/version record, and human review of supported claims.
