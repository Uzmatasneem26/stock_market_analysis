import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import COLORS, EVENTS, get_prepared, page_header, style, worst_day, section

prepared = get_prepared()
page_header("Price Events", "A one-day fall near 50% is a bonus issue, not a loss")

# ---------------------------------------------------------------- worst days
worst = {n: worst_day(d) for n, d in prepared.items()}
rows = [{"Stock": n, "Worst day": dt.date(), "Close": round(px_, 2), "Move %": round(mv, 1)}
        for n, (dt, px_, mv) in worst.items()]
section("Each stock's worst day (raw prices)")
st.dataframe(pd.DataFrame(rows).sort_values("Move %"), hide_index=True, use_container_width=True)
st.caption("The ratios were inferred from the size and shape of the drop and the 1:1 pattern; "
           "not verified against company filings.")

# ----------------------------------------------------------- all six at once
section("All stocks: raw close with the worst day marked")
names = list(prepared.keys())
fig = make_subplots(rows=3, cols=2, subplot_titles=names, vertical_spacing=0.09)
for i, n in enumerate(names):
    r, c = i // 2 + 1, i % 2 + 1
    d = prepared[n]
    dt, px_, mv = worst[n]
    fig.add_trace(go.Scatter(x=d["date"], y=d["raw_close"], showlegend=False,
                             line=dict(color=COLORS.get(n, "#0f2a43"), width=1.4)), row=r, col=c)
    fig.add_trace(go.Scatter(x=[dt], y=[px_], mode="markers+text", showlegend=False,
                             text=[f"{mv:.1f}%"], textposition="top center",
                             marker=dict(color="crimson", size=10, symbol="x")), row=r, col=c)
fig.update_layout(template="plotly_white", height=820, margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------- single stock
section("Inspect one stock")
stock = st.selectbox("Stock", names)
d = prepared[stock]
dt, px_, mv = worst[stock]

c1, c2, c3 = st.columns(3)
c1.metric("Worst day", f"{dt:%Y-%m-%d}")
c2.metric("Close on that day", f"{px_:,.2f}")
c3.metric("One-day move", f"{mv:.1f}%")

if stock in EVENTS:
    ev = EVENTS[stock]
    adj = d["raw_close"].where(d["date"] >= pd.Timestamp(ev["date"]), d["raw_close"] / ev["factor"])
    st.markdown(f"**Bonus issue detected:** event date {ev['date']}, ratio 1:{ev['factor']}. Prices before the "
                "date are divided by 2; the event date is the first day trading at the new level.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["date"], y=d["raw_close"], name="Raw close", line=dict(color="crimson")))
    fig.add_trace(go.Scatter(x=d["date"], y=adj, name="Adjusted close", line=dict(color="royalblue")))
    st.plotly_chart(style(fig, 440, f"{stock}: bonus-issue cliff and its adjustment"), use_container_width=True)
else:
    st.success(f"No price event: {stock}'s worst day is a normal market move, so no adjustment is needed.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["date"], y=d["raw_close"], name="Close", line=dict(color="#0f2a43")))
    fig.add_trace(go.Scatter(x=[dt], y=[px_], mode="markers", name="Worst day",
                             marker=dict(color="crimson", size=12, symbol="x")))
    st.plotly_chart(style(fig, 440, f"{stock}: close with worst day marked"), use_container_width=True)

moves = (100 * d["raw_close"].pct_change()).dropna()
bar = go.Figure(go.Bar(x=d["date"].iloc[1:], y=moves,
                       marker_color=["crimson" if m < 0 else "#2e8b57" for m in moves]))
st.plotly_chart(style(bar, 320, f"{stock}: daily % move"), use_container_width=True)