import streamlit as st

from utils import get_data, get_prepared, page_header, section

data = get_data()
prepared = get_prepared()
page_header("Data Explorer", "Master table, raw data and data-quality checks")

section("Master table")
master = None
for n, d in prepared.items():
    part = d[["date", "close_price"]].rename(columns={"close_price": n})
    master = part if master is None else master.merge(part, on="date", how="inner")
st.caption(f"{len(master)} rows, one per date, closing prices as set in the sidebar")
st.dataframe(master.assign(date=master["date"].dt.date).round(2), hide_index=True, use_container_width=True)
st.download_button("Download master table (CSV)", master.to_csv(index=False), "master_table_output.csv", "text/csv")

section("Raw data")
pick = st.selectbox("Stock", list(data.keys()))
raw = data[pick].copy()
raw["date"] = raw["date"].dt.date
st.dataframe(raw, hide_index=True, use_container_width=True)

section("Data quality")
rows = [{"Stock": n, "Date": r.date.date()} for n, d in data.items()
        for r in d[d["deliverable_qty"].isna()].itertuples()]
if rows:
    st.warning(f"{len(rows)} rows have a missing deliverable quantity.")
    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption("Looks like an exchange reporting gap; it does not affect close prices.")
else:
    st.success("No missing deliverable quantities.")