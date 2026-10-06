import streamlit as st

from utils import get_sqlite, page_header, run_query, section

con = get_sqlite()
page_header("SQL Analysis", "Queries run on an in-memory SQLite database built from the CSV files")

st.markdown(
    """
**Tables**
* `bajaj_auto`, `eicher_motors`, `hero_motocorp`, `infosys`, `tcs`, `tvs_motors`: raw data (`date`, `close_price`, `deliverable_qty`)
* `prices`: all six raw closes in one long table (`stock`, `date`, `close_price`)
* `signals`: closes, `ma20`, `ma50` and `signal` per stock (follows the sidebar settings)
* `master_table`: one row per date with every stock's close
"""
)

QUERIES = {
    "History available (Bajaj Auto)": """
SELECT COUNT(*) AS trading_days, MIN(date) AS first_day, MAX(date) AS last_day
FROM bajaj_auto""",
    "Eicher's five best closes": """
SELECT date, close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5""",
    "TCS average close by year": """
SELECT strftime('%Y', date) AS year, ROUND(AVG(close_price), 2) AS avg_close
FROM tcs
GROUP BY year
ORDER BY year""",
    "Missing deliverable_qty": """
SELECT 'bajaj_auto' AS stock, date FROM bajaj_auto WHERE deliverable_qty IS NULL
UNION ALL SELECT 'eicher_motors', date FROM eicher_motors WHERE deliverable_qty IS NULL
UNION ALL SELECT 'hero_motocorp', date FROM hero_motocorp WHERE deliverable_qty IS NULL
UNION ALL SELECT 'infosys', date FROM infosys WHERE deliverable_qty IS NULL
UNION ALL SELECT 'tcs', date FROM tcs WHERE deliverable_qty IS NULL
UNION ALL SELECT 'tvs_motors', date FROM tvs_motors WHERE deliverable_qty IS NULL""",
    "Signal counts (Bajaj Auto)": """
SELECT signal, COUNT(*) AS days
FROM signals
WHERE stock = 'Bajaj Auto'
GROUP BY signal
ORDER BY signal""",
    "Signal on a given day": """
SELECT stock, date, signal
FROM signals
WHERE date = '2018-06-21'
ORDER BY stock""",
    "Buys and sells for all six stocks": """
SELECT stock,
       SUM(signal = 'Buy')  AS buys,
       SUM(signal = 'Sell') AS sells
FROM signals
GROUP BY stock
ORDER BY stock""",
    "Latest Buy/Sell signal per stock": """
WITH ranked AS (
    SELECT stock, date, signal,
           ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
    FROM signals
    WHERE signal <> 'Hold'
)
SELECT stock, date AS last_signal_date, signal AS last_signal
FROM ranked
WHERE rn = 1
ORDER BY stock""",
    "Who went up? (raw first vs last close)": """
WITH ends AS (
    SELECT stock, MIN(date) AS first_day, MAX(date) AS last_day
    FROM prices GROUP BY stock
)
SELECT e.stock,
       f.close_price AS first_close,
       l.close_price AS last_close,
       ROUND(100.0 * (l.close_price - f.close_price) / f.close_price, 1) AS pct_change
FROM ends e
JOIN prices f ON f.stock = e.stock AND f.date = e.first_day
JOIN prices l ON l.stock = e.stock AND l.date = e.last_day
ORDER BY pct_change DESC""",
    "Each stock's worst day": """
WITH moves AS (
    SELECT stock, date, close_price,
           100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY date) - 1) AS pct_move
    FROM prices
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move) AS rn
    FROM moves WHERE pct_move IS NOT NULL
)
SELECT stock, date, close_price, ROUND(pct_move, 1) AS pct_move
FROM ranked WHERE rn = 1
ORDER BY pct_move""",
    "Adjusted change for TCS and Infosys": """
WITH adjusted AS (
    SELECT 'TCS' AS stock, date,
           CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS adj_close
    FROM tcs
    UNION ALL
    SELECT 'Infosys', date,
           CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END
    FROM infosys
),
ends AS (SELECT stock, MIN(date) AS f, MAX(date) AS l FROM adjusted GROUP BY stock)
SELECT e.stock,
       ROUND(100.0 * (b.adj_close / a.adj_close - 1), 1) AS adjusted_pct_change
FROM ends e
JOIN adjusted a ON a.stock = e.stock AND a.date = e.f
JOIN adjusted b ON b.stock = e.stock AND b.date = e.l
ORDER BY e.stock""",
}

section("Predefined queries")
name = st.selectbox("Choose a query", list(QUERIES.keys()))
sql = QUERIES[name].strip()
st.code(sql, language="sql")
if st.button("Run predefined query", type="primary"):
    try:
        res = run_query(con, sql)
        st.dataframe(res, hide_index=True, use_container_width=True)
        st.download_button("Download result (CSV)", res.to_csv(index=False), "sql_query_results.csv", "text/csv")
    except Exception as e:
        st.error(str(e))

section("Custom SQL")
st.caption("Read-only: a single SELECT or WITH statement.")
custom = st.text_area("Write your query", "SELECT * FROM master_table LIMIT 10", height=160)
if st.button("Run custom query"):
    try:
        res = run_query(con, custom)
        st.success(f"{len(res)} rows returned")
        st.dataframe(res, hide_index=True, use_container_width=True)
        st.download_button("Download result (CSV)", res.to_csv(index=False), "custom_query_results.csv",
                           "text/csv", key="dl_custom")
    except Exception as e:
        st.error(str(e))