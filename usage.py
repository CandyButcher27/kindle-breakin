"""Scan Claude Code session JSONL files and aggregate token usage into SQLite."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

# USD per million tokens, keyed by model. Falls back to a mid-range default.
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-4-1": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-4-5": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-4-6": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-4-8": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-5": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-5-5": {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-sonnet-4": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-sonnet-4-5": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-sonnet-4-6": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-sonnet-5": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-sonnet-5-5": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-haiku-4": {"input": 1.0, "cache_write": 1.25, "cache_read": 0.10, "output": 5.0},
    "claude-haiku-4-5": {"input": 1.0, "cache_write": 1.25, "cache_read": 0.10, "output": 5.0},
    "claude-haiku-5": {"input": 1.0, "cache_write": 1.25, "cache_read": 0.10, "output": 5.0},
    "claude-haiku-5-5": {"input": 1.0, "cache_write": 1.25, "cache_read": 0.10, "output": 5.0},
}

DEFAULT_PRICING = PRICING["claude-sonnet-4-5"]


def model_cost(model: str, input_tokens: int, cache_write: int, cache_read: int, output: int) -> float:
    p = PRICING.get(model, DEFAULT_PRICING)
    return (
        input_tokens * p["input"]
        + cache_write * p["cache_write"]
        + cache_read * p["cache_read"]
        + output * p["output"]
    ) / 1_000_000


@dataclass
class UsageRecord:
    day: str  # YYYY-MM-DD
    model: str
    input_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


def _usage_ts(o: dict) -> str | None:
    ts = o.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(
            timezone.utc
        ).strftime("%Y-%m-%d")
    except ValueError:
        return None


def scan_projects(projects_dir: Path) -> list[UsageRecord]:
    """Read every *.jsonl under projects_dir and aggregate usage per day+model."""
    agg: dict[tuple[str, str], UsageRecord] = {}
    for jsonl in projects_dir.rglob("*.jsonl"):
        try:
            with jsonl.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") != "assistant":
                        continue
                    msg = obj.get("message") or {}
                    usage = msg.get("usage") or {}
                    if not usage:
                        continue
                    day = _usage_ts(obj)
                    if not day:
                        continue
                    model = msg.get("model") or "unknown"
                    rec = agg.setdefault(
                        (day, model),
                        UsageRecord(day=day, model=model),
                    )
                    rec.input_tokens += int(usage.get("input_tokens", 0))
                    rec.cache_write_tokens += int(usage.get("cache_creation_input_tokens", 0))
                    rec.cache_read_tokens += int(usage.get("cache_read_input_tokens", 0))
                    rec.output_tokens += int(usage.get("output_tokens", 0))
                    rec.cost_usd += model_cost(
                        model,
                        int(usage.get("input_tokens", 0)),
                        int(usage.get("cache_creation_input_tokens", 0)),
                        int(usage.get("cache_read_input_tokens", 0)),
                        int(usage.get("output_tokens", 0)),
                    )
        except OSError:
            continue
    return list(agg.values())


def store(records: list[UsageRecord], db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """CREATE TABLE IF NOT EXISTS usage (
                day TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                cache_write_tokens INTEGER NOT NULL,
                cache_read_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                PRIMARY KEY (day, model)
            )"""
        )
        con.executemany(
            """INSERT INTO usage
               (day, model, input_tokens, cache_write_tokens, cache_read_tokens,
                output_tokens, cost_usd)
               VALUES (:day, :model, :input_tokens, :cache_write_tokens,
                       :cache_read_tokens, :output_tokens, :cost_usd)
               ON CONFLICT(day, model) DO UPDATE SET
                   input_tokens=excluded.input_tokens,
                   cache_write_tokens=excluded.cache_write_tokens,
                   cache_read_tokens=excluded.cache_read_tokens,
                   output_tokens=excluded.output_tokens,
                   cost_usd=excluded.cost_usd""",
            [asdict(r) for r in records],
        )
        con.commit()
    finally:
        con.close()


def refresh(db_path: Path, projects_dir: Path) -> int:
    records = scan_projects(projects_dir)
    store(records, db_path)
    return len(records)
