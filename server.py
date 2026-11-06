"""Serve a lightweight Claude Code usage dashboard for a Kindle browser."""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

DB_PATH = Path(__file__).parent / "usage.db"

app = FastAPI(title="Kindle Usage Dashboard")

_REFRESH = 120  # seconds between auto-reloads
_CHART_DAYS = 30
_CHART_H = 300


def _query() -> list[tuple]:
    con = sqlite3.connect(DB_PATH)
    try:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """SELECT day, model, input_tokens, cache_write_tokens,
                      cache_read_tokens, output_tokens, cost_usd
               FROM usage ORDER BY day DESC, cost_usd DESC"""
        ).fetchall()
        return [tuple(r) for r in rows]
    finally:
        con.close()


def _totals(rows: list[tuple]) -> dict:
    total_cost = sum(r[6] for r in rows)
    total_tokens = sum(r[2] + r[3] + r[4] + r[5] for r in rows)
    days = sorted({r[0] for r in rows})
    return {
        "cost": total_cost,
        "tokens": total_tokens,
        "days": len(days),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
    }


@app.get("/api/usage")
def api_usage() -> JSONResponse:
    rows = _query()
    days: dict[str, list[dict]] = {}
    for r in rows:
        day, model = r[0], r[1]
        days.setdefault(day, []).append(
            {
                "model": model,
                "input": r[2],
                "cache_write": r[3],
                "cache_read": r[4],
                "output": r[5],
                "cost": round(r[6], 4),
            }
        )
    return JSONResponse({"totals": _totals(rows), "days": days})


def _pretty_model(model: str) -> str:
    family, *version = model.removeprefix("claude-").split("-")
    return f"{family.title()} {'.'.join(version)}".strip()


def _stats(rows: list[tuple], today: date) -> dict:
    by_day: dict[str, float] = {}
    for r in rows:
        by_day[r[0]] = by_day.get(r[0], 0.0) + r[6]

    def cost(d: date) -> float:
        return by_day.get(d.isoformat(), 0.0)

    month = today.strftime("%Y-%m")
    month_cost = sum(c for d, c in by_day.items() if d.startswith(month))
    week_start = (today - timedelta(days=6)).isoformat()

    models: dict[str, float] = {}
    for r in rows:
        if r[0] >= week_start and r[1] != "<synthetic>":
            name = _pretty_model(r[1])
            models[name] = models.get(name, 0.0) + r[6]

    return {
        "today": cost(today),
        "yesterday": cost(today - timedelta(days=1)),
        "week_avg": sum(cost(today - timedelta(days=i)) for i in range(7)) / 7,
        "month": month_cost,
        "projected": month_cost / today.day * calendar.monthrange(today.year, today.month)[1],
        "chart": [
            (today - timedelta(days=i), cost(today - timedelta(days=i)))
            for i in range(_CHART_DAYS - 1, -1, -1)
        ],
        "models": sorted(models.items(), key=lambda kv: kv[1], reverse=True),
    }


def _chart_html(chart: list[tuple[date, float]]) -> str:
    peak = max((c for _, c in chart), default=0.0) or 1.0
    bars = "".join(
        f"<td><div class='bar' style='height:{max(round(c / peak * _CHART_H), 1 if c else 0)}px'></div></td>"
        for _, c in chart
    )
    first, last = chart[0][0], chart[-1][0]
    return (
        f"<div class='peak'>${peak:.0f}</div>"
        f"<table class='chart' style='height:{_CHART_H}px'><tr>{bars}</tr></table>"
        f"<table class='axis'><tr><td>{first:%b %d}</td>"
        f"<td class='r'>{last:%b %d}</td></tr></table>"
    )


def _models_html(models: list[tuple[str, float]]) -> str:
    if not models:
        return "<div class='l'>No usage this week</div>"
    top = models[0][1] or 1.0
    return "".join(
        f"<table class='m'><tr><td class='mn'>{name}</td>"
        f"<td><div class='hbar' style='width:{max(c / top * 100, 1):.0f}%'></div></td>"
        f"<td class='mc'>${c:.2f}</td></tr></table>"
        for name, c in models
    )


@app.get("/", response_class=HTMLResponse)
def dashboard(rotate: int = 0) -> str:
    rows = _query()
    s = _stats(rows, datetime.now(timezone.utc).date())
    updated = datetime.fromtimestamp(DB_PATH.stat().st_mtime).strftime("%b %d %H:%M")
    rot = rotate if rotate in (90, 270) else 0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="{_REFRESH}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Usage</title>
<style>
  html, body {{ margin:0; padding:0; background:#fff; color:#000;
        font-family:Helvetica, Arial, sans-serif; }}
  #w {{ padding:20px 24px; box-sizing:border-box; }}
  .r90 #w, .r270 #w {{ position:absolute; top:0; left:0;
        -webkit-transform-origin:0 0; transform-origin:0 0; }}
  .r90 #w {{ -webkit-transform:rotate(90deg) translateY(-100%);
            transform:rotate(90deg) translateY(-100%); }}
  .r270 #w {{ -webkit-transform:rotate(-90deg) translateX(-100%);
             transform:rotate(-90deg) translateX(-100%); }}
  .cols {{ display:table; width:100%; table-layout:fixed; }}
  .left, .right {{ display:table-cell; vertical-align:top; }}
  .left {{ width:38%; padding-right:24px; border-right:3px solid #000; }}
  .right {{ padding-left:24px; }}
  .l {{ font-size:15px; font-weight:bold; text-transform:uppercase; letter-spacing:1px; }}
  .hero {{ font-size:84px; font-weight:bold; line-height:1; margin:4px 0 20px; }}
  .grid {{ width:100%; border-collapse:collapse; }}
  .grid td {{ border-top:2px solid #000; padding:10px 0; width:50%; vertical-align:top; }}
  .v {{ font-size:32px; font-weight:bold; }}
  .upd {{ font-size:14px; margin-top:16px; }}
  .peak {{ font-size:14px; font-weight:bold; }}
  .chart {{ width:100%; table-layout:fixed; border-collapse:collapse;
           border-bottom:3px solid #000; margin-top:4px; }}
  .chart td {{ vertical-align:bottom; padding:0 1px; }}
  .bar {{ background:#000; }}
  .axis {{ width:100%; font-size:14px; margin-bottom:22px; }}
  .axis .r {{ text-align:right; }}
  .m {{ width:100%; table-layout:fixed; border-collapse:collapse; margin-top:8px; }}
  .m td {{ padding:2px 0; vertical-align:middle; }}
  .mn {{ width:130px; font-size:18px; font-weight:bold; }}
  .mc {{ width:100px; font-size:18px; font-weight:bold; text-align:right; }}
  .hbar {{ background:#000; height:18px; }}
</style>
</head>
<body class="r{rot}">
<div id="w">
<div class="cols">
  <div class="left">
    <div class="l">Today (UTC)</div>
    <div class="hero">${s['today']:.2f}</div>
    <table class="grid">
      <tr><td><div class="l">Yesterday</div><div class="v">${s['yesterday']:.2f}</div></td>
          <td><div class="l">7-day avg</div><div class="v">${s['week_avg']:.2f}</div></td></tr>
      <tr><td><div class="l">Month</div><div class="v">${s['month']:.0f}</div></td>
          <td><div class="l">Projected</div><div class="v">${s['projected']:.0f}</div></td></tr>
    </table>
    <div class="upd">Data as of {updated}</div>
  </div>
  <div class="right">
    <div class="l">Last {_CHART_DAYS} days</div>
    {_chart_html(s['chart'])}
    <div class="l">This week by model</div>
    {_models_html(s['models'])}
  </div>
</div>
</div>
<script>
if ({rot} && window.innerHeight > 0) {{
  document.getElementById('w').style.width = window.innerHeight + 'px';
}}
</script>
</body>
</html>"""


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
