"""Smoke test for the FastAPI server scaffold.

Exercises every endpoint against a temporary `runs/` directory so the
test does not depend on the committed demo run. The server is read-only
and stateless beyond the filesystem; this gives us coverage of the
JSON-shape contract without booting uvicorn.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "20260101T000000Z_deadbeef"
    run_dir.mkdir(parents=True)
    (run_dir / "config.yaml").write_text("name: test\nstrategy: trend_following\n")
    (run_dir / "metrics.json").write_text(json.dumps({"sharpe": 1.23, "max_drawdown": 0.05}))
    (run_dir / "equity_curve.csv").write_text("ts,equity\n2024-01-01,1000000.0\n2024-01-02,1010000.0\n")
    (run_dir / "decisions.jsonl").write_text(
        '{"ts":"2024-01-01","regime":"trending","notes":"first"}\n'
    )

    monkeypatch.setenv("PRAXIS_RUNS_DIR", str(runs_dir))

    # Server reads PRAXIS_RUNS_DIR per-request via _runs_dir(), so a simple
    # env override is enough — no module reload trickery needed.
    from praxis.server import app

    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version(client: TestClient) -> None:
    r = client.get("/version")
    assert r.status_code == 200
    assert "version" in r.json()


def test_strategies(client: TestClient) -> None:
    r = client.get("/strategies")
    assert r.status_code == 200
    body = r.json()
    assert "trend_following" in body
    assert "stat_arb" in body
    assert "vol_target" in body


def test_runs_listing(client: TestClient) -> None:
    r = client.get("/runs")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["id"] == "20260101T000000Z_deadbeef"
    assert body[0]["metrics"]["sharpe"] == pytest.approx(1.23)


def test_run_detail(client: TestClient) -> None:
    r = client.get("/runs/20260101T000000Z_deadbeef")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "20260101T000000Z_deadbeef"
    assert body["metrics"]["max_drawdown"] == pytest.approx(0.05)
    assert "config_yaml" in body
    assert len(body["decisions"]) == 1
    assert body["decisions"][0]["regime"] == "trending"


def test_run_equity(client: TestClient) -> None:
    r = client.get("/runs/20260101T000000Z_deadbeef/equity")
    assert r.status_code == 200
    points = r.json()
    assert len(points) == 2
    assert points[0]["equity"] == pytest.approx(1_000_000.0)
    assert points[1]["ts"] == "2024-01-02"


def test_unknown_run_404(client: TestClient) -> None:
    r = client.get("/runs/does-not-exist")
    assert r.status_code == 404
