"""FastAPI server exposing live agent state to the operator terminal.

This is a minimal scaffold; the full live wiring (websocket-streaming
decisions, paper-trade tick ingestion) lands in v0.2 per docs/ROADMAP.md.

Run:
    poetry run uvicorn praxis.server:app --host 0.0.0.0 --port 8000

The Next.js terminal reads `NEXT_PUBLIC_API_URL=http://<host>:8000` on
the client side. When unset, the terminal falls back to deterministic
seeded demo data — both modes render identically, which keeps the UI
truthful when the backend is offline.
"""
from praxis.server.app import app

__all__ = ["app"]
