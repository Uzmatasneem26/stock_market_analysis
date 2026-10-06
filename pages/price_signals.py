import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import get_prepared, page_header, settings, style, badge, section

prepared = get_prepared()
_, fast, slow = settings()
page_header("Price & Signals", "Buy = fast average crosses above slow; Sell = crosses below")

c1, c2 = st.columns([1, 2])
stock = c1.selectbox("Stock", list(prepared.keys()))
d_all = prepared[stock]
lo, hi = d_all["date"].min().date(), d_all["date"].max().date()
rng = c2.slider("Date range", lo, hi, (lo, hi))
d = d_all[(d_all["date"] >= pd.Timestamp(rng[0])) & (d_all["date"] <= pd.Timestamp(rng[1]))]

fig = go.Figure()
fig.add_trace(go.Scatter(x=d["date"], y=d["close_price"], name="Close", line=dict(color="#9aa0a6", width=1)))
fig.add_trace(go.Scatter(x=d["date"], y=d["ma_fast"], name=f"{fast}-day MA", line=dict(color="#1a73e8")))
fig.add_trace(go.Scatter(x=d["date"], y=d["ma_slow"], name=f"{slow}-day MA", line=dict(color="#f57c00")))
for sig, sym, col in (("Buy", "triangle-up", "green"), ("Sell", "triangle-down", "red")):
    s = d[d["signal"] == sig]
    fig.add_trace(go.Scatter(x=s["date"], y=s["close_price"], mode="markers", name=sig,
                             marker=dict(symbol=sym, size=12, color=col)))
st.plotly_chart(style(fig, 520, f"{stock}: close, moving averages and signals"), use_container_width=True)

section("Signal summary")
sig = d_all[d_all["signal"] != "Hold"]
a, b, c = st.columns(3)
a.metric("Buys", int((d_all["signal"] == "Buy").sum()))
b.metric("Sells", int((d_all["signal"] == "Sell").sum()))
c.markdown("**Last signal**", help="Most recent Buy or Sell")
if len(sig):
    c.markdown(badge(sig["signal"].iloc[-1], f"{sig['signal'].iloc[-1]} · {sig['date'].iloc[-1]:%d %b %Y}"),
               unsafe_allow_html=True)

st.subheader("Signal log")
log = sig[["date", "close_price", "ma_fast", "ma_slow", "signal"]].copy()
log["date"] = log["date"].dt.date
st.dataframe(log.round(2).rename(columns={"ma_fast": f"MA{fast}", "ma_slow": f"MA{slow}"}),
             hide_index=True, use_container_width=True)

st.subheader("Signal on a given day")
default_day = min(max(pd.Timestamp("2018-06-21").date(), lo), hi)
day = st.date_input("Date", default_day, min_value=lo, max_value=hi)
row = d_all[d_all["date"] == pd.Timestamp(day)]
if row.empty:
    st.info("No trading data for that date (market closed).")
else:
    r = row.iloc[0]
    x, y = st.columns(2)
    x.metric("Signal", r["signal"])
    y.metric("Close", f"{r['close_price']:,.2f}")