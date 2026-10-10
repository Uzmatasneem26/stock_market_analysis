# Stock Market Analytics

A multipage Streamlit dashboard that analyses six NSE stocks (Bajaj Auto, Eicher Motors, Hero Motocorp,
Infosys, TCS, TVS Motors) from 1 Jan 2015 to 31 Jul 2018, built from a SQL stock-market analysis project.

## Objective
Find which stocks gained or lost, test a 20/50-day moving-average (golden cross) rule against buy-and-hold,
and catch data problems such as bonus issues that look like losses.

### Business Problem
Investors and analysts often face challenges interpreting historical stock market data, identifying price trends, and evaluating stock performance manually. The lack of clear and interactive visualizations can make it difficult to understand market fluctuations and compare performance over time.

### Business Value
This project simplifies stock market data analysis by converting raw financial data into interactive visualizations and performance indicators, helping users understand historical market behavior more effectively.

### Business Use Cases
* Stock performance monitoring :Track historical stock prices and performance.

* Trend analysis : Identify upward, downward, and sideways price movements.

* Volatility analysis	Understand the extent of price fluctuations.

* Trading volume analysis	Examine changes in trading activity over time.

* Historical comparison	Compare stock performance across different periods.

* Investment research	Provide historical insights to support further research and decision-making.

## Dataset
Six daily CSVs with at least `Date` and `Close Price` (and `Deliverable Quantity` for the data-quality check).

## Pages
* **Home**: KPIs, performance table, growth chart, project notes
* **Live Prices**: current NSE prices for the six companies (Yahoo Finance, delayed), 52-week range, volume and today's golden-cross status
* **Price & Signals**: price, moving averages, Buy/Sell markers, signal log, signal-on-a-date lookup
* **Returns Analysis**: raw vs adjusted change, yearly averages, five best closes
* **Strategy Backtest**: compounded trades vs buy-and-hold, whipsaws, trade list
* **Price Events**: TCS (2018-05-31) and Infosys (2015-06-15) 1:1 bonus-issue cliffs
* **SQL Analysis**: predefined and custom read-only queries on in-memory SQLite
* **Data Explorer**: master table, raw data, missing `deliverable_qty` dates

Sidebar settings apply to every page: bonus-issue adjustment toggle and the fast/slow moving-average windows.

## SQL
CSVs are loaded into an in-memory SQLite database. Tables: `bajaj_auto`, `eicher_motors`, `hero_motocorp`,
`infosys`, `tcs`, `tvs_motors` (raw), `prices`, `signals`, `master_table`. The original analysis was written
for MySQL 8; the queries here are the SQLite equivalents (`strftime` instead of `YEAR`).

## Project structure
```text
stock_market_app/
├── app.py            # config, CSS, sidebar settings, navigation
├── utils.py          # loading, signals, backtest, SQLite
├── data/             # the six CSV files
├── pages/
│   ├── home.py
│   ├── live_prices.py
│   ├── price_signals.py
│   ├── returns_analysis.py
│   ├── backtest.py
│   ├── price_events.py
│   ├── sql_analysis.py
│   └── data_explorer.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Run locally
```bash
python -m venv venv
venv\Scripts\activate        # Windows (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
streamlit run app.py
```
Place `bajaj_auto.csv`, `eicher_motors.csv`, `hero_motocorp.csv`, `infosys.csv`, `tcs.csv` and
`tvs_motors.csv` in `data/` (or upload them from the sidebar).

## Deploy
Push `app.py`, `utils.py`, `requirements.txt`, `data/` and `pages/` to GitHub, then deploy on Streamlit
Community Cloud with `app.py` as the main file.

## Live prices
The Live Prices page uses the `yfinance` package (Yahoo Finance, about 15 minutes delayed, cached for 5 minutes). It needs internet access, which Streamlit Community Cloud provides. Live prices are split/bonus-adjusted by Yahoo, so they are not directly comparable to the 2015-2018 CSV closes.

 