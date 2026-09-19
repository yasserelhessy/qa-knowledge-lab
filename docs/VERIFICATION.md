# Local verification evidence

Verified on 2026-09-19 with Python 3.12.14 on macOS. Exact installed demo/test dependencies are in `requirements-lock.txt`.

| Check | Result |
|---|---|
| Editable installation and dependency resolution | Passed |
| API, unit, contract, fake-model and evaluator tests | 24 passed |
| Standalone demo golden evaluation | 12/12 passed; exit 0 |
| First runnable teaching example | Correct two-line output |
| Uvicorn startup | Passed on 127.0.0.1:8000 |
| Live HTTP health, supported answer, refusal and input validation | Passed |
| Browser JavaScript syntax (`node --check`) | Passed |
| Dependency consistency (`pip check`) | Passed |
| Four Playwright Chromium tests | Blocked before execution: browser launch failed |
| Visual desktop/mobile inspection | Blocked by browser environment |
| Hosted GitHub Actions | Prepared, not executed |
| Paid real-model invocation | Not performed |

The Chromium download succeeded. Browser launch raised `TargetClosedError` with a SIGTRAP and macOS power-notification registration error before any test could execute. The separate Codex browser surface also failed during kernel startup with a `sandbox-exec` TIOCSTI configuration error. These failures do not establish either a pass or an application failure for the browser workflows. Run the documented browser command on a normal local environment or execute the included GitHub Actions workflow to complete that gate. No screenshots were fabricated.

A dependency emits a deprecation warning concerning Starlette's use of AnyIO's `BlockingPortal` alias. The tests pass; the warning originates in the pinned dependency combination, not application code.

`reports/sample-demo.json` is actual evaluator output. The delivered test report XML files capture the API/unit pass and the browser startup errors. They may include local machine paths; omit generated reports when publishing if desired. No demo result is a claim about general LLM safety or live-model reliability.
