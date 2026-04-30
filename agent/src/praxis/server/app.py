"""FastAPI app — read-only views of the most-recent run + tail of the
audit log. Designed so the Next.js operator terminal can swap from seeded
demo data to live state by setting `NEXT_PUBLIC_API_URL`.

Endpoints:

* `GET  /health`          liveness probe
* `GET  /version`         build metadata
* `GET  /strategies`      strategies registered in the engine
* `GET  /runs`            list of recorded runs (newest first)
* `GET  /runs/{run_id}`   metrics + config + last 100 decisions of one run
* `GET  /runs/{run_id}/equity`     equity curve as JSON timeseries

This file is intentionally small and dependency-light — no DB, no auth.
v0.2 adds a websocket for streaming decisions and per-bar marks.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from praxis import __version__
from praxis.strategies import REGISTRY as STRATEGY_REGISTRY

log = logging.getLogger(__name__)

def _runs_dir() -> Path:
    return Path(os.getenv("PRAXIS_RUNS_DIR", "runs"))

app = FastAPI(
    title="praxis-server",
    version=__version__,
    description="Read-only live state for the Praxis operator terminal.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("PRAXIS_CORS_ORIGINS", "*").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__}


@app.get("/strategies")
def strategies() -> list[str]:
    return list(STRATEGY_REGISTRY)


def _list_runs() -> list[Path]:
    runs_dir = _runs_dir()
    if not runs_dir.exists():
        return []
    return sorted([p for p in runs_dir.iterdir() if p.is_dir()], reverse=True)


@app.get("/runs")
def runs() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for run in _list_runs():
        metrics_path = run / "metrics.json"
        if not metrics_path.exists():
            continue
        try:
            metrics = json.loads(metrics_path.read_text())
        except json.JSONDecodeError:
            metrics = {}
        out.append({
            "id": run.name,
            "metrics": metrics,
        })
    return out


@app.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    run = _runs_dir() / run_id
    if not run.exists() or not run.is_dir():
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    payload: dict[str, Any] = {"id": run_id}

    metrics_path = run / "metrics.json"
    if metrics_path.exists():
        payload["metrics"] = json.loads(metrics_path.read_text())

    config_path = run / "config.yaml"
    if config_path.exists():
        payload["config_yaml"] = config_path.read_text()

    decisions_path = run / "decisions.jsonl"
    if decisions_path.exists():
        tail: list[dict[str, Any]] = []
        with decisions_path.open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    tail.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        payload["decisions"] = tail[-100:]
    return payload


@app.get("/runs/{run_id}/equity")
def run_equity(run_id: str) -> list[dict[str, Any]]:
    run = _runs_dir() / run_id
    equity = run / "equity_curve.csv"
    if not equity.exists():
        raise HTTPException(status_code=404, detail="equity_curve.csv not found")
    out: list[dict[str, Any]] = []
    with equity.open() as fh:
        next(fh, None)  # header
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                out.append({"ts": parts[0], "equity": float(parts[1])})
            except ValueError:
                continue
    return out


@app.get("/runs/{run_id}/decisions/stream")
async def run_decisions_stream(
    run_id: str, replay_delay_ms: int = 200, loop: bool = True
) -> StreamingResponse:
    """Server-Sent Events stream of decisions.jsonl.

    The recorded decision log is replayed at `replay_delay_ms` per line;
    when the file is exhausted the stream loops by default so the operator
    terminal always shows recent activity. A future v0.2 will tail-follow
    a live paper-trade run instead of replaying.
    """
    run = _runs_dir() / run_id
    decisions_path = run / "decisions.jsonl"
    if not decisions_path.exists():
        raise HTTPException(status_code=404, detail="decisions.jsonl not found")

    async def event_source() -> AsyncIterator[bytes]:
        delay = max(0.0, replay_delay_ms / 1000.0)
        while True:
            with decisions_path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    yield f"data: {line}\n\n".encode()
                    if delay:
                        await asyncio.sleep(delay)
            if not loop:
                return
            yield b": loop-restart\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
