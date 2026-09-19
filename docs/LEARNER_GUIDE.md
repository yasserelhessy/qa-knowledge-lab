# Yasser's learner guide

This project bridges skills you already use—test fixtures, API contracts, Playwright and release gates—to Python and AI components. Read **one step per session**. Predict, run, explain, change, then move on. You do not need to learn embeddings or agents first.

## Step 1 — Runnables, invoke, and output parsing

Open `examples/01_runnables.py`. Run it from the repository root:

```bash
python examples/01_runnables.py
```

The important lines are:

```python
normalize = RunnableLambda(lambda text: text.strip().lower())
make_message = RunnableLambda(lambda text: AIMessage(content=f"You asked: {text}"))
chain = normalize | make_message | StrOutputParser()
print(normalize.invoke("  API Tests  "))
print(chain.invoke("  API Tests  "))
```

Take each idea separately:

1. `lambda text: ...` is a small Python function. `strip()` removes outer spaces; `lower()` lowercases characters.
2. `RunnableLambda` wraps that function in LangChain's standard runnable interface. You can invoke both a single component and a whole composition the same way.
3. `.invoke(input)` executes one input and returns one output. It is an ordinary method call, not a promise that a model or network is involved.
4. `AIMessage` represents the shape of a chat model response. Here **we construct it ourselves**; no AI generation occurs.
5. `|` connects runnables: the string from `normalize` becomes the input to `make_message`; its message becomes the parser input.
6. `StrOutputParser()` extracts textual content. It changes representation. It does not validate correctness, citations, or safety.

Expected output:

```text
api tests
You asked: api tests
```

Trace the types: `str → str → AIMessage → str`. Change `.lower()` to `.upper()`, predict both lines, and rerun. Restore the change afterward. Explain aloud why `chain.invoke(...)` returns a string even though `make_message` returns a message.

**Stop here until this feels clear.** Your next session starts with Step 2.

## Step 2 — Understand the local evidence

Open `data/knowledge.json`. It is a JSON array, which Python loads as a list of dictionaries. Each record contains:

- `id`: stable machine-readable citation key, such as `retry`.
- `title`: source label shown to the user.
- `text`: the evidence and, in demo mode, the complete answer.
- `keywords`: a deliberately small searchable vocabulary.

The six topics are release gates, synthetic fixtures, payment retries, order contracts, incident ownership, and evaluation policy. They describe a fictional team. There are no customer records or private company policies.

Why JSON? You can inspect changes in Git without running a database. Why separate keywords from text? It makes the matching rules visible, although it also creates maintenance work and potential dataset bias. This is a teaching retriever, not a semantic search engine.

Exercise: locate the payment retry count in the source. Predict which golden case should fail if you change it.

## Step 3 — Follow retrieval

Open `app/retrieval.py`.

- `DATA` is computed from the module's path. The working directory does not decide where documents are loaded.
- `STOP` removes common question words so that words like “the” do not determine the result.
- `tokens()` lowercases, extracts alphanumeric tokens using a regular expression, and returns a set. Repeated words count once. It does not stem words or understand synonyms.
- `load_documents()` reads JSON. Its optional path supports isolated test inputs.
- `retrieve()` computes the fraction of query tokens that match each document's keywords, chooses the highest-scoring record, and rejects it below `0.6`.
- The return dictionary keeps `question`, `document`, and `score` together for the next runnable. When no evidence is selected, `document` is `None`.

Example: “What are the release gates?” becomes `{release, gates}`. Both tokens match the release record, giving `2/2 = 1.0`. Unknown words reduce coverage. Ties choose the first record in the file; this is deterministic but not a relevance guarantee. An empty corpus returns no document.

Why one document? It keeps citations and data flow easy to follow. Multiple documents would require ranking, context budgets, and attribution rules. Why a threshold? It creates an explicit refusal path, but lexical overlap is not proof that the question is answerable. Mixed questions can still fool it.

Exercise: compare `Assistant().invoke("release gates")` with `Assistant().invoke("penguins")` in a Python shell.

## Step 4 — Read the typed API objects

Open `app/models.py`.

`Question` is a Pydantic model. `Field(min_length=3, max_length=500)` bounds the input. `ConfigDict(extra="forbid")` rejects unexpected request fields instead of silently accepting them. The `meaningful` validator strips outer spaces and rejects whitespace-only input that otherwise meets the raw length check. Its classmethod receives the validated string and returns the normalized value.

`Source` defines the citation's ID, title, and excerpt. `Answer` declares answer text, a two-value status, a list of sources, demo/live mode, and retrieval score. `Literal` limits acceptable values. These objects help FastAPI validate responses and generate API documentation. A typed answer can still be factually wrong: schema checks and evidence checks solve different problems.

Why explicit schemas? They serve the same purpose as DTOs in a Java API automation framework and make consumer expectations visible.

Exercise: POST a request with an unexpected `mode` field and inspect the 422 response. The caller cannot switch the server into a paid model mode through this API.

## Step 5 — Follow the real project chain

Open `app/chain.py`. Read it in this order:

### Initialization and dependency injection

`Assistant.__init__` validates mode and loads documents unless a corpus was explicitly passed. The `documents is None` check matters: an empty list is a valid test corpus and must remain empty. `model` injection lets tests provide a fake runnable without credentials.

The demo generator is:

```python
RunnableLambda(lambda item: AIMessage(content=item["context"])) | self.parser
```

It returns source text inside a chat message, then parses it. This preserves the message-to-string learning boundary while being honest that no model is invoked.

### Optional model composition

The `openai` branch lazily imports `ChatOpenAI`, so the optional package is not required for demo use. It checks credentials and uses a configured model name, bounded timeout, and one retry. Temperature zero reduces variation but does not guarantee determinism.

`ChatPromptTemplate` creates system and human messages. `{context}` and `{question}` are placeholders filled at invocation time. The system message tells the model to use evidence and gives an exact refusal sentence. A prompt is an instruction, not a security boundary.

```python
prompt | model | self.parser
```

This is the same composition pattern as Step 1 with a real generation step substituted. The adapter contract is tested with a fake model; live API quality remains unverified.

### Retrieval followed by response construction

`self.chain` composes a retrieval runnable and `self.respond`. `respond()` checks whether evidence exists **before** invoking a generator. Unsupported retrieval returns the fixed refusal without making a provider call.

For evidence, the generator receives a dictionary containing the original question and source text. Exact refusal output or empty model text results in a refused response with no citations. Otherwise the response includes the chosen source. Arbitrary wording such as a model's alternate refusal sentence is not specially recognized—one limitation of a string-output contract.

Finally `invoke()` forwards to the composed chain. The public method returns a typed `Answer`, while the inner generator returns a string. Keeping those boundaries separate helps tests pinpoint failures.

Exercise: draw the values passed between the two runnables for one supported and one unsupported question.

## Step 6 — See how HTTP reaches the chain

Open `app/main.py`.

- `STATIC` locates the UI assets.
- `create_app(assistant=None)` is an application factory. Tests inject a fresh assistant or a deliberately failing fake; production reads `QA_MODE` at startup.
- `FastAPI(...)` provides routing, schema validation, and OpenAPI documentation.
- `/static` serves CSS and JavaScript; `/` serves the HTML file.
- `GET /api/health` reports mode and corpus size. This is local process readiness, not a remote-model connectivity check.
- `POST /api/ask` receives a validated `Question`, invokes the service, and serializes the typed `Answer`.
- The exception boundary returns a generic 502 rather than raw provider diagnostics. That prevents accidental secret exposure; production would also need controlled, redacted logging.
- `app = create_app()` exposes the ASGI object that Uvicorn imports.

Why synchronous routes? The pipeline is synchronous and FastAPI runs normal route functions in a thread pool. This avoids putting blocking provider work directly inside an async event loop in this small app. It is not an unlimited scaling design.

Exercise: compare an invalid request (422), a supported question (200 answered), and an unknown question (200 refused). Refusal is a successful domain response, not an HTTP server error.

## Step 7 — Understand the interface

### `app/static/index.html`

The document head sets language, character encoding, viewport, stylesheet, and a deferred script. Semantic `header`, `main`, `section`, `aside`, and `footer` elements organize the page. The title and badges identify the project and runtime mode. Suggested-question buttons only populate the text area; the user explicitly submits.

The form has a real label, required input, and length bounds. `#error` uses `role="alert"`; `#result` uses `aria-live="polite"` to announce answers. Stable IDs connect the small JavaScript file to the DOM. The sidebar explains the pipeline without claiming a measured pass rate.

### `app/static/style.css`

The root defines system fonts and the green/cream palette, avoiding network fonts. Global sizing makes dimensions predictable. The shell caps reading width. The workspace uses a two-column grid on desktop; the media query changes it to one column below 760px. Focus outlines make keyboard interaction visible. Source details, form status, and disabled buttons have distinct visual treatment. Visual browser verification was blocked by the local browser launch environment; see the verification notes.

### `app/static/app.js`

The initial health request sets the demo/live badge. Suggestion listeners copy data attributes into the input. The submit handler prevents page navigation, clears the previous result/error, disables duplicate submissions, and sends JSON with `fetch`.

An abort timeout prevents an indefinite waiting state. HTTP 422 gets an input-specific message; other failures get a retry message. Successful data is rendered with `textContent` and newly created DOM elements. No model output goes through `innerHTML`. Sources become expandable `details` elements. `finally` restores the button after success or failure.

Why vanilla JavaScript? The UI needs one form and one result. A frontend framework, build server, and package manager would add concepts before improving this learning goal. Python serves the assets and API from one origin.

Exercise: use the unknown-question button and confirm that no previous citation remains visible.

## Step 8 — Read the API and unit tests

### `tests/conftest.py`

Pytest discovers fixtures automatically. `assistant` creates a fresh demo instance per test. `client` creates a FastAPI `TestClient` around an injected instance and closes it with a context manager. This tests HTTP routing/validation in-process without needing a server or model key.

### `tests/test_api.py`

The health assertion checks mode and source count. The answer test validates actual JSON against an independently stored schema, then checks a known citation. Parameterization covers six invalid payloads without duplicating test bodies. Additional cases cover malformed JSON, refusal, a sanitized provider failure, and asset serving.

### `tests/answer.schema.json`

This committed JSON Schema is a consumer contract, independent of FastAPI's generated schema. Required fields, types, allowed values, numeric bounds, and rejected extra properties make accidental API drift visible. Do not regenerate it silently whenever server code changes; review a contract change intentionally.

### `tests/test_chain.py`

The tests isolate evidence extraction, an empty corpus, fixture isolation, threshold boundary behavior, optional model prompt construction and parsing, bypassing a model when retrieval refuses, blank/exact model refusal, and invalid mode. Fake runnables implement a small behavior instead of contacting a real provider.

Why both unit and HTTP tests? Unit tests localize logic failures. HTTP tests catch request and serialization issues around the same logic. Browser tests then add user interactions and rendering.

Exercise: change the retrieval threshold from `0.6` to `0.7` and see the boundary test fail. Restore it.

## Step 9 — Learn the evaluation gate

### `data/golden.json`

Each case has `id`, `question`, expected `status`, exact `source_ids`, and `required` answer fragments. There are seven supported cases (including case/spacing variation) and five unsupported cases, including an instruction attack and near-topic questions. A small synthetic golden set is a regression fixture, not a statistical benchmark.

### `app/evaluate.py`

`evaluate()` invokes the assistant once per case and records four booleans: expected status, exact citations, required facts, and exact extractive grounding. Exceptions become failed rows containing only the exception class, keeping secrets out of reports. The result includes mode, total, pass count, and per-case evidence.

`main()` reads CLI options, loads cases, writes indented JSON, prints the result, and exits nonzero if any case fails or the dataset is empty. The `if __name__ == "__main__"` guard allows both importing the evaluator in tests and running it as a command.

The grounding comparison is intentionally narrow: answer equals citation excerpt. Valid real-model paraphrases may fail; a citation alone never establishes truth. An unsupported response must also satisfy expected refusal status, empty citation IDs, and refusal wording in the golden expectations.

### `tests/test_evaluation.py`

One test runs the actual corpus through every case. Two tests inject faulty assistants: invented answers and wrong facts with a correct citation. This demonstrates that the gate detects selected failures, rather than merely reporting a happy-path score.

### `reports/sample-demo.json`

A checked-in result from a verified demo evaluation. Generated `latest.json` is ignored so routine test runs do not create source diffs. The sample records responses and individual check results for review.

Exercise: change one golden required fact to an impossible phrase. Run the evaluator and inspect its failed row and process exit code (`echo $?` on macOS/Linux). Restore the case.

## Step 10 — Follow the browser tests

Open `tests/e2e/test_ui.py`.

`pytestmark` labels this module as e2e. `BASE_URL` is configurable, defaulting to the local server. The Playwright plugin supplies a fresh `page` fixture. User-facing labels and button roles are preferred for interactions; stable IDs identify result regions. `expect` assertions retry automatically until conditions are met, avoiding arbitrary sleeps.

The four workflows cover:

1. A successful release question and expanded source evidence.
2. An unknown question with no citation.
3. An intercepted 502, visible error, enabled retry button, and successful recovery against the real API.
4. A mobile viewport, no horizontal overflow, and an HTML-like response rendered as text.

The first two use the actual running server. Fault injection intentionally mocks only the relevant response in the latter tests. This makes rare errors reproducible while preserving real application behavior for core flows.

Exercise: remove the final button reset temporarily; the recovery test should expose the regression. Restore it.

## Step 11 — Configuration and continuous integration

### `pyproject.toml`

The build section uses setuptools. Project metadata declares supported Python and runtime dependencies. Optional `test` dependencies supply pytest, the HTTP client, Playwright, and JSON Schema validation. Optional `openai` installs the provider integration only when requested. Package discovery includes `app`; static files are package data. The app still needs this editable checkout for its corpus. Pytest configuration declares its test folder and e2e marker.

### `requirements-lock.txt`

Exact versions exported from the verified demo/test environment. CI installs these before installing the project without dependency resolution, reducing version drift. This is a version pin file, not a hash-verified supply-chain lock. Rebuild it in a clean environment when updating dependencies and rerun the suite. It does not pin the optional remote-model adapter.

### `.env.example`

Configuration documentation without credentials. Demo is the default. Values must be exported into the shell; no dotenv loader is present. Model configuration belongs on the server, never in browser JavaScript.

### `.gitignore`

Excludes environment directories, Python caches, editable-install metadata, `.env`, test artifacts and generated reports. Explicitly preserves the sample report. Ignoring secrets is only a safeguard—never put real credentials in project files.

### `.github/workflows/quality.yml`

The workflow runs on push/pull request using Ubuntu/Python 3.12. It installs the lock, the local package, and Chromium, then runs API/unit tests and evaluation. A background Uvicorn process supports browser tests. A bounded readiness loop waits for the health endpoint; a shell trap cleans up the server. JUnit reports and failure traces/screenshots are uploaded even on failure. A timeout limits hung builds. The job stays in demo mode and uses no provider secrets.

Why a separate evaluator step if pytest already checks the dataset? Pytest localizes regression failures; the standalone CLI produces a durable report and models a reusable deployment gate.

Exercise: after you create your own GitHub repository, inspect the first workflow run and download its artifact. Local success alone does not prove hosted CI success.

## Step 12 — Explain the whole project

`app/__init__.py` marks the application package and states its purpose. `README.md` is the entry point for another engineer: run, verify, architecture, limitations and truthful resume wording. `docs/TEST_STRATEGY.md` records risks, gates and scope. `docs/VERIFICATION.md` records actual local evidence and boundaries.

You can now explain the complete path:

> A validated HTTP question enters a LangChain runnable sequence. A simple local retriever selects evidence or refuses. A demo generator or optional model produces a message, the parser converts it to text, and a typed response carries the answer and citation to the UI. Tests verify both behavior and boundaries, while a finite dataset supplies a repeatable regression gate.

Then explain three limits: lexical matching is fragile, parsing is not verification, and passing synthetic demo tests says nothing conclusive about general LLM reliability.

Next increment: ask a colleague to write unseen questions. Measure retrieval failures before selecting a more complex retriever. Let the tests motivate the architecture change.
