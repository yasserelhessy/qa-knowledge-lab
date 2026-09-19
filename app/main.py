import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.chain import Assistant
from app.models import Answer, Question

STATIC = Path(__file__).parent / "static"

def create_app(assistant=None):
    service = assistant if assistant is not None else Assistant(os.getenv("QA_MODE", "demo"))
    api = FastAPI(title="QA Knowledge Lab", version="1.0.0")
    api.mount("/static", StaticFiles(directory=STATIC), name="static")

    @api.get("/", include_in_schema=False)
    def home():
        return FileResponse(STATIC / "index.html")

    @api.get("/api/health")
    def health():
        return {"status": "ok", "mode": service.mode, "documents": len(service.documents)}

    @api.post("/api/ask", response_model=Answer)
    def ask(payload: Question):
        try:
            return service.invoke(payload.question)
        except Exception:
            # Keep provider errors and possible credentials out of public responses.
            raise HTTPException(502, "Answer service unavailable. Please retry.") from None

    return api

app = create_app()
