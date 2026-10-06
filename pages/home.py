import plotly.graph_objects as go
import streamlit as st

from utils import COLORS, badge, get_prepared, page_header, section, settings, style, summary_table

prepared = get_prepared()
use_adj, fast, slow = settings()
ov = summary_table(prepared)

page_header("Stock Market Analytics",
            f"Golden-cross analysis of six NSE stocks · {fast}-day vs {slow}-day moving average")

first = next(iter(prepared.values()))
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stocks analysed", len(prepared))
c2.metric("Trading days", f"{len(first):,}")
c3.metric("Period", f"{first['date'].min():%b %Y} – {first['date'].max():%b %Y}")
c4.metric("Signals", f"{ov['Buys'].sum()} Buys · {ov['Sells'].sum()} Sells")

section("Performance at a glance", "First close vs last close; sorted best to worst")
cards = []
for _, r in ov.iterrows():
    chg = r["Change % (selected)"]
    cls = "up" if chg >= 0 else "down"
    arrow = "▲" if chg >= 0 else "▼"
    sig_name = str(r["Last signal"]).split(",")[0]
    cards.append(
        f'<div class="stock-card" style="--c:{COLORS.get(r["Stock"], "#0f2a43")}">'
        f'<div class="name">{r["Stock"]}</div>'
        f'<div class="pct {cls}">{arrow} {chg:+.1f}%</div>'
        f'<div class="sub">{r["First close"]:,.2f} → {r["Last close"]:,.2f}</div>'
        f'<div style="margin-top:8px">{badge(sig_name, "Last: " + str(r["Last signal"]))}</div>'
        f'</div>'
    )
st.markdown('<div class="card-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
if not use_adj:
    st.warning("Raw prices are selected. TCS and Infosys look like big losers only because of their "
               "bonus issues. Turn on the adjustment in the sidebar to see the real picture.")
st.caption("Percent change compares the first and last trading day and ignores dividends.")

section("Full comparison")
st.dataframe(
    ov, hide_index=True, use_container_width=True,
    column_config={
        "Raw change %": st.column_config.NumberColumn(format="%.1f%%"),
        "Change % (selected)": st.column_config.NumberColumn(format="%.1f%%"),
        "First close": st.column_config.NumberColumn(format="%.2f"),
        "Last close": st.column_config.NumberColumn(format="%.2f"),
    },
)

section("Growth of 100", "Every stock rebased to 100 on its first close")
fig = go.Figure()
for n, d in prepared.items():
    fig.add_trace(go.Scatter(x=d["date"], y=100 * d["close_price"] / d["close_price"].iloc[0], name=n,
                             line=dict(color=COLORS.get(n), width=2)))
st.plotly_chart(style(fig, 440), use_container_width=True)

section("About this project")
st.markdown(
    """
**Objective.** Use daily price data to find which stocks gained or lost, test a moving-average
crossover rule, and spot data problems that distort the picture.

**Questions answered**
* Which stocks gained the most over the period?
* How often did the golden-cross rule trigger, and did it beat buy-and-hold?
* Which stocks produced whipsaws (signals reversed within 30 trading days)?
* Are there price events, like bonus issues, that look like losses but are not?

**Pages**
* **Price & Signals**: price, moving averages and Buy/Sell markers per stock
* **Returns Analysis**: raw vs adjusted change, yearly averages, best closes
* **Strategy Backtest**: compounded signal trades vs buy-and-hold
* **Price Events**: the TCS and Infosys bonus-issue cliffs, plus every stock's worst day
* **SQL Analysis**: predefined and custom queries on an in-memory SQLite database
* **Data Explorer**: master table, raw data and data-quality checks
"""
)
with st.expander("Limitations"):
    st.markdown(
        """
* Percent changes ignore dividends; no brokerage, tax or slippage in the backtest.
* About 3.6 years of data and six to eleven trades per stock is a small sample.
* Results depend on the chosen moving-average windows.
* Bonus-issue ratios were inferred from the size and shape of the price drop, not verified against filings.
* The analysis describes patterns and is not investment advice.
"""
    )