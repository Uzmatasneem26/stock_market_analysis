import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import EVENTS, adjust, get_data, get_prepared, page_header, pct_change, style, section

prepared = get_prepared()
data = get_data()
page_header("Returns Analysis", "First close vs last close, before and after adjusting for bonus issues")

df = pd.DataFrame({
    "Stock": list(data.keys()),
    "Raw change %": [pct_change(data[n]) for n in data],
    "Adjusted change %": [pct_change(adjust(data[n], n, True)) for n in data],
}).sort_values("Adjusted change %", ascending=False).round(1)

fig = go.Figure()
fig.add_trace(go.Bar(x=df["Stock"], y=df["Raw change %"], name="Raw", marker_color="#c0392b"))
fig.add_trace(go.Bar(x=df["Stock"], y=df["Adjusted change %"], name="Adjusted", marker_color="#0f2a43"))
fig.update_layout(barmode="group")
st.plotly_chart(style(fig, 420, "Total change by stock"), use_container_width=True)
st.dataframe(df, hide_index=True, use_container_width=True)
moved = [s for s in df["Stock"] if s in EVENTS]
if moved:
    st.info(" and ".join(moved) + ": raw and adjusted differ because a 1:1 bonus issue halved the "
            "price overnight without any real loss.")

section("Average close by year")
pick = st.selectbox("Stock", list(prepared.keys()), key="yr_stock")
d = prepared[pick]
yearly = d.groupby(d["date"].dt.year)["close_price"].mean().reset_index()
yearly.columns = ["year", "avg_close"]
fig = px.bar(yearly, x="year", y="avg_close", text_auto=".0f")
fig.update_layout(xaxis=dict(type="category"))
st.plotly_chart(style(fig, 360, f"{pick}: average close per year"), use_container_width=True)
st.caption("2018 contains only seven months of data.")

section("Five best closes")
top = d.nlargest(5, "close_price")[["date", "close_price"]]
top["date"] = top["date"].dt.date
st.dataframe(top.round(2), hide_index=True, use_container_width=True)