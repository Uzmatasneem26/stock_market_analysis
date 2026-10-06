import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import COLORS, TICKERS, add_signals, badge, page_header, section, settings, style

try:
    import yfinance as yf
except ImportError:
    st.error("The `yfinance` package is missing. Add `yfinance` to requirements.txt and redeploy.")
    st.stop()

page_header("Live Prices", "Latest NSE prices for the six companies · Yahoo Finance, about 15 minutes delayed")
_, fast, slow = settings()


@st.cache_data(ttl=300, show_spinner=False)
def fetch(ticker: str):
    """5 years of daily data; cached for 5 minutes. Returns None if Yahoo gives nothing."""
    try:
        df = yf.Ticker(ticker).history(period="5y", interval="1d", auto_adjust=True)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    return df[["Date", "Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"]).reset_index(drop=True)


top = st.columns([4, 1])
top[0].caption("Prices refresh every 5 minutes. Outside market hours you will see the last close "
               "(NSE trades 9:15 to 15:30 IST, Monday to Friday).")
if top[1].button("Refresh now", use_container_width=True):
    fetch.clear()
    st.rerun()

with st.spinner("Fetching latest prices..."):
    hist = {n: fetch(t) for n, t in TICKERS.items()}

ok = {n: d for n, d in hist.items() if d is not None and len(d) > 2}
if not ok:
    st.warning("Could not fetch prices right now. Yahoo Finance may be rate-limiting or the app has no internet "
               "access. Try 'Refresh now' in a minute.")
    st.stop()
missing = [n for n in TICKERS if n not in ok]
if missing:
    st.warning("No data returned for: " + ", ".join(missing))


def quote(d: pd.DataFrame) -> dict:
    last, prev = d["Close"].iloc[-1], d["Close"].iloc[-2]
    yr = d.tail(252)
    return {
        "price": last, "chg": last - prev, "pct": 100 * (last / prev - 1),
        "hi": yr["High"].max(), "lo": yr["Low"].min(), "vol": d["Volume"].iloc[-1],
        "asof": d["Date"].iloc[-1],
    }


quotes = {n: quote(d) for n, d in ok.items()}
asof = max(q["asof"] for q in quotes.values())
st.markdown(f"**Latest trading day in data:** {asof:%d %b %Y}")

# ------------------------------------------------------------------ cards
section("Current prices", "Latest close or live price, with change vs the previous trading day")
cards = []
for n, q in quotes.items():
    cls = "up" if q["pct"] >= 0 else "down"
    arrow = "▲" if q["pct"] >= 0 else "▼"
    pos = (q["price"] - q["lo"]) / (q["hi"] - q["lo"]) * 100 if q["hi"] > q["lo"] else 50
    cards.append(
        f'<div class="stock-card" style="--c:{COLORS.get(n, "#0f2a43")}">'
        f'<div class="name">{n} <span style="color:#94a3b8;font-weight:500;font-size:12px">{TICKERS[n]}</span></div>'
        f'<div class="pct" style="color:#0f2a43">₹{q["price"]:,.2f}</div>'
        f'<div class="{cls}" style="font-weight:700">{arrow} {q["chg"]:+,.2f} ({q["pct"]:+.2f}%)</div>'
        f'<div class="sub" style="margin-top:8px">52-week range ₹{q["lo"]:,.0f} – ₹{q["hi"]:,.0f}</div>'
        f'<div style="background:#e2e8f0;border-radius:999px;height:6px;margin-top:4px">'
        f'<div style="width:{pos:.0f}%;background:{COLORS.get(n, "#0f2a43")};height:6px;border-radius:999px"></div></div>'
        f'<div class="sub" style="margin-top:6px">Volume {q["vol"]:,.0f}</div>'
        f'</div>'
    )
st.markdown('<div class="card-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)

section("All companies")
tbl = pd.DataFrame([{
    "Stock": n, "Symbol": TICKERS[n], "Price (₹)": round(q["price"], 2), "Change": round(q["chg"], 2),
    "Change %": round(q["pct"], 2), "52w low": round(q["lo"], 2), "52w high": round(q["hi"], 2),
    "Volume": int(q["vol"]),
} for n, q in quotes.items()]).sort_values("Change %", ascending=False)
st.dataframe(tbl, hide_index=True, use_container_width=True,
             column_config={"Change %": st.column_config.NumberColumn(format="%.2f%%")})

# ----------------------------------------------------------------- detail
section("Price chart", f"With the same {fast}/{slow}-day moving averages and golden-cross signals as the rest of the app")
c1, c2 = st.columns(2)
stock = c1.selectbox("Company", list(ok.keys()))
period = c2.selectbox("Period", ["1 month", "3 months", "6 months", "1 year", "3 years", "5 years"], index=3)
days = {"1 month": 30, "3 months": 91, "6 months": 182, "1 year": 365, "3 years": 1095, "5 years": 1826}[period]

d = ok[stock].rename(columns={"Date": "date", "Close": "close_price"})
d = add_signals(d, fast, slow)  # computed on the full 5 years so averages exist for short periods
view = d[d["date"] >= d["date"].max() - pd.Timedelta(days=days)]

q = quotes[stock]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Price", f"₹{q['price']:,.2f}", f"{q['pct']:+.2f}%")
m2.metric("Day range", f"₹{view['Low'].iloc[-1]:,.0f} – ₹{view['High'].iloc[-1]:,.0f}")
m3.metric("Period change", f"{100 * (view['close_price'].iloc[-1] / view['close_price'].iloc[0] - 1):+.1f}%")
trend_up = pd.notna(d["ma_fast"].iloc[-1]) and pd.notna(d["ma_slow"].iloc[-1]) and d["ma_fast"].iloc[-1] > d["ma_slow"].iloc[-1]
m4.metric("Short vs long average", "Fast above slow" if trend_up else "Fast below slow")

sig = d[d["signal"] != "Hold"]
if len(sig):
    st.markdown("**Latest golden-cross signal:** " +
                badge(sig["signal"].iloc[-1], f"{sig['signal'].iloc[-1]} · {sig['date'].iloc[-1]:%d %b %Y}"),
                unsafe_allow_html=True)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.04)
col = COLORS.get(stock, "#0f2a43")
fig.add_trace(go.Scatter(x=view["date"], y=view["close_price"], name="Close", line=dict(color=col, width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=view["date"], y=view["ma_fast"], name=f"{fast}-day MA", line=dict(color="#1a73e8", width=1.3)), row=1, col=1)
fig.add_trace(go.Scatter(x=view["date"], y=view["ma_slow"], name=f"{slow}-day MA", line=dict(color="#f57c00", width=1.3)), row=1, col=1)
for name, sym, c in (("Buy", "triangle-up", "green"), ("Sell", "triangle-down", "red")):
    s = view[view["signal"] == name]
    fig.add_trace(go.Scatter(x=s["date"], y=s["close_price"], mode="markers", name=name,
                             marker=dict(symbol=sym, size=11, color=c)), row=1, col=1)
fig.add_trace(go.Bar(x=view["date"], y=view["Volume"], name="Volume", marker_color="#cbd5e1", showlegend=False), row=2, col=1)
st.plotly_chart(style(fig, 560, f"{stock} ({TICKERS[stock]})"), use_container_width=True)

st.caption("Live prices come from Yahoo Finance and are adjusted for splits and bonus issues, so they are not directly "
           "comparable with the 2015-2018 CSV closes used elsewhere in this app. Data may be delayed or incomplete. "
           "Not investment advice.")