"""
QUANT FOUNDS — TradingView Webhook Bridge Server (FastAPI + SQLite)
Receives live alerts from TradingView Pine Script v6 and serves the QUANT FOUNDS Dashboard.
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

WEBHOOK_SECRET = os.getenv("QF_WEBHOOK_SECRET", "QF_SECRET_2026")
DB_PATH = Path(__file__).parent / "quant_founds.db"
INDEX_PATH = Path(__file__).parent / "index.html"

app = FastAPI(title="QUANT FOUNDS TradingView Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                received_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                direction TEXT NOT NULL,
                state TEXT NOT NULL,
                score REAL NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()


@app.get("/")
def serve_dashboard():
    if INDEX_PATH.exists():
        return FileResponse(INDEX_PATH)
    return {"status": "ok", "service": "QUANT FOUNDS Bridge"}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook/tradingview")
async def receive_tradingview_webhook(
    request: Request,
    token: Optional[str] = Query(default=None),
):
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload from TradingView")

    provided_token = token or payload.get("token")
    if WEBHOOK_SECRET and provided_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret token")

    required = ["symbol", "entry", "sl", "tp2"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")

    signal_id = str(payload.get("signal_id") or f"QF-TV-{uuid.uuid4().hex[:8].upper()}")
    payload["signal_id"] = signal_id
    received_at = datetime.now(timezone.utc).isoformat()
    payload["received_at"] = received_at

    symbol = str(payload["symbol"]).upper()
    timeframe = str(payload.get("timeframe", "15"))
    direction = "SELL" if str(payload.get("direction", "BUY")).upper() == "SELL" else "BUY"
    sig_state = str(payload.get("state", "ENTRY_READY"))
    score = float(payload.get("score", 80))

    # Strip token before saving/broadcasting
    safe_payload = {k: v for k, v in payload.items() if k != "token"}

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO signals
            (signal_id, received_at, symbol, timeframe, direction, state, score, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (signal_id, received_at, symbol, timeframe, direction, sig_state, score, json.dumps(safe_payload, ensure_ascii=False)),
        )
        conn.commit()

    return {"status": "accepted", "signal_id": signal_id, "symbol": symbol, "direction": direction}


@app.get("/api/signals/latest")
def get_latest_signals(
    limit: int = Query(default=20, ge=1, le=100),
    x_qf_token: Optional[str] = Header(default=None),
):
    if WEBHOOK_SECRET and x_qf_token and x_qf_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid X-QF-Token header")

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM signals ORDER BY received_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    items: List[Dict[str, Any]] = [json.loads(r[0]) for r in rows]
    return {"latest": items[0] if items else None, "history": items, "count": len(items)}
