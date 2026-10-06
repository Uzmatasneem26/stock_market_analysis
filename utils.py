"""Shared helpers: data loading, signal logic, backtest, SQLite build."""
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

STOCKS = {
    "Bajaj Auto": "bajaj_auto",
    "Eicher Motors": "eicher_motors",
    "Hero Motocorp": "hero_motocorp",
    "Infosys": "infosys",
    "TCS": "tcs",
    "TVS Motors": "tvs_motors",
}

# Yahoo Finance symbols for the live-prices page
TICKERS = {
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Eicher Motors": "EICHERMOT.NS",
    "Hero Motocorp": "HEROMOTOCO.NS",
    "Infosys": "INFY.NS",
    "TCS": "TCS.NS",
    "TVS Motors": "TVSMOTOR.NS",
}

# 1:1 bonus issues. Closes BEFORE the event date are divided by `factor`.
EVENTS = {
    "TCS": {"date": "2018-05-31", "factor": 2},
    "Infosys": {"date": "2015-06-15", "factor": 2},
}


# ---------------------------------------------------------------- loading
def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"[^a-z0-9]+", "_", c.strip().lower()).strip("_") for c in df.columns]
    rename = {}
    for c in df.columns:
        if c in ("close", "close_price"):
            rename[c] = "close_price"
        elif c.startswith("deliverable_q"):
            rename[c] = "deliverable_qty"
    df = df.rename(columns=rename)
    if "date" not in df.columns or "close_price" not in df.columns:
        raise ValueError(f"Need 'Date' and 'Close Price' columns, found: {list(df.columns)}")
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date")
    if "deliverable_qty" not in df.columns:
        df["deliverable_qty"] = np.nan
    return df.reset_index(drop=True)


KEYWORDS = {
    "Bajaj Auto": "bajaj",
    "Eicher Motors": "eicher",
    "Hero Motocorp": "hero",
    "Infosys": "infosys",
    "TCS": "tcs",
    "TVS Motors": "tvs",
}


def match_stock(filename: str):
    """Match any reasonable file name ('Bajaj Auto.csv', 'bajaj_auto.csv', 'TVS-Motors.csv') to a stock."""
    norm = re.sub(r"[^a-z0-9]", "", Path(filename).stem.lower())
    for name, key in KEYWORDS.items():
        if key in norm:
            return name
    return None


def _csv_files(folder: Path):
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() == ".csv")


@st.cache_data(show_spinner=False)
def _load_folder(files: tuple) -> dict:
    out = {}
    for path, _mtime in files:
        name = match_stock(path)
        if name:
            out[name] = _clean(pd.read_csv(path))
    return out


def load_uploads(files) -> dict:
    out = {}
    for f in files:
        name = match_stock(f.name)
        if name:
            out[name] = _clean(pd.read_csv(f))
    return out


def get_data() -> dict:
    files = tuple((str(p), p.stat().st_mtime) for p in _csv_files(DATA_DIR))
    data = dict(_load_folder(files))
    data.update(st.session_state.get("uploaded_data", {}))
    # keep the canonical stock order
    return {n: data[n] for n in STOCKS if n in data}


def require_data() -> dict:
    data = get_data()
    if not data:
        st.warning("No data found. Add the six CSV files to the `data/` folder "
                   "or upload them from the sidebar.")
        st.stop()
    return data


def settings():
    s = st.session_state
    return s.get("use_adj", True), int(s.get("fast", 20)), int(s.get("slow", 50))


# --------------------------------------------------------------- analysis
def adjust(df: pd.DataFrame, stock: str, on: bool) -> pd.DataFrame:
    df = df.copy()
    df["raw_close"] = df["close_price"]
    if on and stock in EVENTS:
        ev = EVENTS[stock]
        df.loc[df["date"] < pd.Timestamp(ev["date"]), "close_price"] /= ev["factor"]
    return df


def add_signals(df: pd.DataFrame, fast: int, slow: int) -> pd.DataFrame:
    df = df.copy()
    df["ma_fast"] = df["close_price"].rolling(fast, min_periods=fast).mean()
    df["ma_slow"] = df["close_price"].rolling(slow, min_periods=slow).mean()
    pf, ps = df["ma_fast"].shift(), df["ma_slow"].shift()
    ok = df[["ma_fast", "ma_slow"]].notna().all(axis=1) & pf.notna() & ps.notna()
    buy = ok & (df["ma_fast"] > df["ma_slow"]) & (pf <= ps)
    sell = ok & (df["ma_fast"] < df["ma_slow"]) & (pf >= ps)
    df["signal"] = np.select([buy, sell], ["Buy", "Sell"], default="Hold")
    return df


@st.cache_data(show_spinner=False)
def prepare_all(_data: dict, use_adj: bool, fast: int, slow: int, _key: int) -> dict:
    return {n: add_signals(adjust(d, n, use_adj), fast, slow) for n, d in _data.items()}


def get_prepared() -> dict:
    data = require_data()
    adj, fast, slow = settings()
    key = sum(len(d) for d in data.values())
    return prepare_all(data, adj, fast, slow, key)


def backtest(df: pd.DataFrame, cost_pct: float = 0.0):
    """Closed Buy->Sell pairs at that day's close; an open final Buy is ignored.
    cost_pct is charged on each side (entry and exit), in percent."""
    c = cost_pct / 100
    trades, entry = [], None
    for r in df[df["signal"] != "Hold"].itertuples():
        if r.signal == "Buy" and entry is None:
            entry = r
        elif r.signal == "Sell" and entry is not None:
            trades.append({
                "buy_date": entry.date, "buy_price": entry.close_price,
                "sell_date": r.date, "sell_price": r.close_price,
                "return_pct": 100 * (r.close_price * (1 - c) / (entry.close_price * (1 + c)) - 1),
            })
            entry = None
    t = pd.DataFrame(trades, columns=["buy_date", "buy_price", "sell_date", "sell_price", "return_pct"])
    comp = (np.prod(1 + t["return_pct"] / 100) - 1) * 100 if len(t) else 0.0
    return t, float(comp)


def whipsaws(df: pd.DataFrame, window: int = 30) -> int:
    pos = {d: i for i, d in enumerate(df["date"])}
    s = list(df[df["signal"] != "Hold"].itertuples())
    return sum(1 for a, b in zip(s, s[1:]) if a.signal != b.signal and pos[b.date] - pos[a.date] <= window)


def worst_day(df: pd.DataFrame):
    mv = df.assign(pct_move=100 * df["raw_close"].pct_change()).dropna(subset=["pct_move"])
    r = mv.loc[mv["pct_move"].idxmin()]
    return r["date"], r["raw_close"], r["pct_move"]


def pct_change(df: pd.DataFrame, col="close_price") -> float:
    return 100 * (df[col].iloc[-1] / df[col].iloc[0] - 1)


def summary_table(prepared: dict) -> pd.DataFrame:
    rows = []
    for n, d in prepared.items():
        sig = d[d["signal"] != "Hold"]
        last = f"{sig['signal'].iloc[-1]}, {sig['date'].iloc[-1].date()}" if len(sig) else "-"
        rows.append({
            "Stock": n,
            "First close": round(d["raw_close"].iloc[0], 2),
            "Last close": round(d["raw_close"].iloc[-1], 2),
            "Raw change %": round(pct_change(d, "raw_close"), 1),
            "Change % (selected)": round(pct_change(d), 1),
            "Buys": int((d["signal"] == "Buy").sum()),
            "Sells": int((d["signal"] == "Sell").sum()),
            "Last signal": last,
        })
    return pd.DataFrame(rows).sort_values("Change % (selected)", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------------- SQL
def build_sqlite(data: dict, prepared: dict) -> sqlite3.Connection:
    """In-memory SQLite mirroring the MySQL project's tables.

    Raw tables (bajaj_auto ... tvs_motors) hold unadjusted data, like the SQL file.
    prices / signals / master_table follow the sidebar settings.
    """
    con = sqlite3.connect(":memory:", check_same_thread=False)

    def prep(df):
        out = df.copy()
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        return out

    for name, stem in STOCKS.items():
        if name in data:
            prep(data[name])[["date", "close_price", "deliverable_qty"]].to_sql(stem, con, index=False)

    prices = pd.concat([prep(d).assign(stock=n)[["stock", "date", "close_price"]]
                        for n, d in data.items()])
    prices.to_sql("prices", con, index=False)

    sig = pd.concat([prep(d).assign(stock=n)[["stock", "date", "close_price", "ma_fast", "ma_slow", "signal"]]
                     for n, d in prepared.items()]).rename(columns={"ma_fast": "ma20", "ma_slow": "ma50"})
    sig.to_sql("signals", con, index=False)

    master = None
    for n, d in prepared.items():
        part = prep(d)[["date", "close_price"]].rename(columns={"close_price": n})
        master = part if master is None else master.merge(part, on="date")
    master.to_sql("master_table", con, index=False)
    return con


@st.cache_resource(show_spinner=False)
def _sqlite(_data, _prepared, key):
    return build_sqlite(_data, _prepared)


def get_sqlite():
    data = require_data()
    adj, fast, slow = settings()
    prepared = get_prepared()
    return _sqlite(data, prepared, (adj, fast, slow, sum(len(d) for d in data.values())))


FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum)\b", re.I)


def run_query(con: sqlite3.Connection, sql: str) -> pd.DataFrame:
    s = sql.strip().rstrip(";")
    if not re.match(r"^(select|with)\b", s, re.I) or FORBIDDEN.search(s) or ";" in s:
        raise ValueError("Only a single read-only SELECT / WITH query is allowed.")
    return pd.read_sql_query(s, con)


# ------------------------------------------------------------------- UI
COLORS = {
    "Bajaj Auto": "#1f77b4",
    "Eicher Motors": "#e4572e",
    "Hero Motocorp": "#2a9d8f",
    "Infosys": "#8e6bbf",
    "TCS": "#f2a541",
    "TVS Motors": "#5c6b73",
}


def page_header(title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="hero"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)


def section(title: str, caption: str = ""):
    cap = f'<span class="section-cap">{caption}</span>' if caption else ""
    st.markdown(f'<div class="section-title">{title}{cap}</div>', unsafe_allow_html=True)


def badge(signal: str, text: str = "") -> str:
    cls = {"Buy": "buy", "Sell": "sell"}.get(signal, "hold")
    return f'<span class="badge badge-{cls}">{text or signal}</span>'


def style(fig, height=440, title=None):
    fig.update_layout(
        template="plotly_white", height=height, hovermode="x unified",
        margin=dict(l=10, r=10, t=56 if title else 20, b=10),
        title=dict(text=title, font=dict(size=16, color="#0f2a43")) if title else None,
        colorway=list(COLORS.values()),
        font=dict(family="Inter, Segoe UI, sans-serif", color="#334155"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.15),
    )
    fig.update_xaxes(gridcolor="#eef1f4", zeroline=False)
    fig.update_yaxes(gridcolor="#eef1f4", zeroline=False)
    return fig