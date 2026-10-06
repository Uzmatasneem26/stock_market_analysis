import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import backtest, get_prepared, page_header, pct_change, style, whipsaws, section

prepared = get_prepared()
page_header("Strategy Backtest", "Closed Buy → Sell pairs, traded at that day's close and compounded")
st.caption("An open final Buy is not counted. No brokerage, tax or dividends. Whipsaw = a signal reversed "
           "within 30 trading days.")

rows = []
for n, d in prepared.items():
    t, comp = backtest(d)
    rows.append({
        "Stock": n, "Trades": len(t), "Wins": int((t["return_pct"] > 0).sum()),
        "Whipsaws": whipsaws(d), "Compounded %": round(comp, 1),
        "Buy & hold %": round(pct_change(d), 1),
        "Worst trade %": round(t["return_pct"].min(), 1) if len(t) else None,
    })
bt = pd.DataFrame(rows)

lagging = int((bt["Compounded %"] < bt["Buy & hold %"]).sum())
c1, c2, c3 = st.columns(3)
c1.metric("Rule lagged buy-and-hold", f"{lagging} of {len(bt)} stocks")
c2.metric("Total trades", int(bt["Trades"].sum()))
c3.metric("Total whipsaws", int(bt["Whipsaws"].sum()))

fig = go.Figure()
fig.add_trace(go.Bar(x=bt["Stock"], y=bt["Compounded %"], name="Golden-cross trades", marker_color="#0f2a43"))
fig.add_trace(go.Bar(x=bt["Stock"], y=bt["Buy & hold %"], name="Buy & hold", marker_color="#8fb8de"))
fig.update_layout(barmode="group")
st.plotly_chart(style(fig, 420, "Strategy vs buy-and-hold"), use_container_width=True)
st.dataframe(bt, hide_index=True, use_container_width=True)

section("Trade list")
stock = st.selectbox("Stock", list(prepared.keys()))
t, _ = backtest(prepared[stock])
if len(t):
    t = t.assign(buy_date=t["buy_date"].dt.date, sell_date=t["sell_date"].dt.date).round(2)
    st.dataframe(t, hide_index=True, use_container_width=True)
else:
    st.info("No closed trades with the current settings.")
st.caption("Small samples and sensitivity to the window choice mean these results are indicative only.")