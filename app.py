import streamlit as st

from utils import STOCKS, get_data, load_uploads

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Stock Market Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stMarkdown, button, input, textarea {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    #MainMenu, footer { visibility: hidden; }

    .stApp { background: linear-gradient(180deg, #f4f7fb 0%, #eef2f7 100%); }
    .block-container { max-width: 1700px; padding-top: 1.6rem; padding-bottom: 3rem; }

    /* ---------- hero banner ---------- */
    .hero {
        background: linear-gradient(120deg, #0b2239 0%, #14527d 55%, #2a9d8f 100%);
        border-radius: 18px; padding: 28px 34px; margin-bottom: 22px;
        box-shadow: 0 10px 28px rgba(15, 42, 67, 0.22);
    }
    .hero h1 { color: #fff !important; font-size: 34px !important; font-weight: 800 !important;
               letter-spacing: -0.5px; margin: 0 !important; padding: 0 !important; }
    .hero p { color: rgba(255,255,255,0.82); margin: 8px 0 0 0; font-size: 16px; }

    /* ---------- section titles ---------- */
    .section-title {
        font-size: 22px; font-weight: 700; color: #0f2a43; margin: 30px 0 12px 0;
        padding-left: 12px; border-left: 5px solid #2a9d8f;
    }
    .section-cap { display: block; font-size: 13px; font-weight: 400; color: #64748b; margin-top: 2px; }
    h2 { font-size: 24px !important; font-weight: 700 !important; color: #0f2a43; margin-top: 1.6rem !important; }
    h3 { font-size: 19px !important; font-weight: 600 !important; color: #1e3a52; }

    /* ---------- sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b2239 0%, #123a5c 100%);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] h1 { font-size: 22px !important; font-weight: 800 !important; }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
        border-radius: 10px; margin-bottom: 4px; transition: background 0.15s ease;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
        background-color: rgba(255, 255, 255, 0.10);
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: linear-gradient(90deg, rgba(42,157,143,0.55), rgba(255,255,255,0.10));
        border-left: 4px solid #2a9d8f;
    }

    /* ---------- metric cards ---------- */
    div[data-testid="stMetric"] {
        background: white; border-radius: 14px; padding: 18px 20px;
        border: 1px solid #e3e8ef; border-top: 4px solid #2a9d8f;
        box-shadow: 0 4px 14px rgba(15, 42, 67, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(15,42,67,0.12); }
    div[data-testid="stMetricLabel"] { font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 800; color: #0f2a43; }
    /* show the full value instead of cutting it off with "..." */
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] > div {
        white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.25;
    }

    /* ---------- stock cards ---------- */
    .card-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 6px 0 10px 0; }
    .stock-card {
        background: white; border-radius: 14px; padding: 16px 18px; border: 1px solid #e3e8ef;
        box-shadow: 0 4px 14px rgba(15, 42, 67, 0.06); border-left: 6px solid var(--c);
    }
    .stock-card .name { font-weight: 700; color: #0f2a43; font-size: 16px; }
    .stock-card .pct { font-size: 30px; font-weight: 800; margin: 6px 0 2px 0; }
    .stock-card .sub { font-size: 12.5px; color: #64748b; }
    .up { color: #15803d; } .down { color: #b91c1c; }
    @media (max-width: 900px) { .card-grid { grid-template-columns: 1fr; } }

    /* ---------- badges ---------- */
    .badge { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 12px;
             font-weight: 700; letter-spacing: .3px; }
    .badge-buy { background: #dcfce7; color: #166534; }
    .badge-sell { background: #fee2e2; color: #991b1b; }
    .badge-hold { background: #e2e8f0; color: #475569; }

    /* ---------- misc ---------- */
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px; font-weight: 600; border: 1px solid #cbd5e1;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #14527d, #2a9d8f); border: none; color: white;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 12px; overflow: hidden; border: 1px solid #e3e8ef;
        box-shadow: 0 4px 14px rgba(15, 42, 67, 0.05);
    }
    div[data-testid="stPlotlyChart"] {
        background: white; border-radius: 14px; padding: 8px; border: 1px solid #e3e8ef;
        box-shadow: 0 4px 14px rgba(15, 42, 67, 0.05);
    }
    div[data-testid="stExpander"] { background: white; border-radius: 12px; border: 1px solid #e3e8ef; }
    hr { margin: 1.5rem 0; }

    /* ---------- hover-to-open sidebar (desktop only) ----------
       Delete this whole block to get the normal always-visible sidebar back. */
    @media (hover: hover) and (min-width: 801px) {
        section[data-testid="stSidebar"] {
            position: fixed !important; top: 0; left: 0; height: 100vh !important;
            width: 300px !important; min-width: 300px !important; margin-left: 0 !important;
            transform: translateX(calc(-100% + 22px)) !important;
            transition: transform 0.28s ease, box-shadow 0.28s ease;
            z-index: 1000000 !important;
        }
        section[data-testid="stSidebar"]:hover,
        section[data-testid="stSidebar"]:focus-within {
            transform: translateX(0) !important;
            box-shadow: 8px 0 30px rgba(11, 34, 57, 0.35);
        }
        /* little handle that stays visible while the sidebar is tucked away */
        section[data-testid="stSidebar"]::after {
            content: "›"; position: absolute; right: 5px; top: 50%;
            color: #ffffff; font-size: 26px; font-weight: 700; opacity: 0.85;
            transition: opacity 0.2s ease;
        }
        section[data-testid="stSidebar"]:hover::after,
        section[data-testid="stSidebar"]:focus-within::after { opacity: 0; }
        /* the manual collapse / expand buttons are not needed any more */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] { display: none !important; }
        .block-container { padding-left: 3.2rem; padding-right: 3.2rem; }
    }

    /* ---------- hover-to-open sidebar (desktop only) ---------- */
    @media (min-width: 992px) {
        /* the sidebar keeps only a slim strip in the page layout, so content gets the full width */
        section[data-testid="stSidebar"] {
            width: 18px !important; min-width: 18px !important; max-width: 18px !important;
            position: relative; z-index: 1000; overflow: visible !important;
        }
        /* the real sidebar panel floats on top and slides in on hover */
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] > div:first-child {
            position: fixed !important; top: 0; left: 0; height: 100vh;
            width: 300px !important; max-width: 300px !important;
            transform: translateX(-282px);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            background: linear-gradient(180deg, #0b2239 0%, #123a5c 100%);
            overflow-y: auto; z-index: 1001;
        }
        section[data-testid="stSidebar"]:hover [data-testid="stSidebarContent"],
        section[data-testid="stSidebar"]:hover > div:first-child {
            transform: translateX(0);
            box-shadow: 8px 0 30px rgba(0, 0, 0, 0.35);
        }
        /* little hint arrow on the slim strip */
        section[data-testid="stSidebar"]::after {
            content: "\00BB"; position: fixed; left: 4px; top: 50%; z-index: 1002;
            color: rgba(255,255,255,0.85); font-size: 20px; font-weight: 700; pointer-events: none;
            transition: opacity 0.15s ease;
        }
        section[data-testid="stSidebar"]:hover::after { opacity: 0; }
        /* the manual collapse/expand buttons are no longer needed */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] { display: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SIDEBAR: title + global settings (shared by every page)
# ---------------------------------------------------------
with st.sidebar:
    st.title("Stock Market Analytics")
    st.caption("Six NSE stocks · 2015 to 2018")

# ---------------------------------------------------------
# NAVIGATION
# ---------------------------------------------------------
pg = st.navigation(
    [
        st.Page("pages/home.py", title="Home", default=True),
        st.Page("pages/live_prices.py", title="Live Prices"),
        st.Page("pages/price_signals.py", title="Price & Signals"),
        st.Page("pages/returns_analysis.py", title="Returns Analysis"),
        st.Page("pages/backtest.py", title="Strategy Backtest"),
        st.Page("pages/price_events.py", title="Price Events"),
        st.Page("pages/sql_analysis.py", title="SQL Analysis"),
        st.Page("pages/data_explorer.py", title="Data Explorer"),
    ]
)

with st.sidebar:
    st.markdown("---")
    st.subheader("Settings")
    loaded = get_data()
    missing = [n for n in STOCKS if n not in loaded]
    if missing:
        st.warning(f"Loaded {len(loaded)} of 6 stocks. Missing: {', '.join(missing)}")
        ups = st.file_uploader("Upload stock CSVs", type="csv", accept_multiple_files=True)
        if ups:
            st.session_state["uploaded_data"] = load_uploads(ups)
            st.rerun()
    else:
        st.caption("All 6 stocks loaded")
    st.toggle("Adjust TCS & Infosys for bonus issues", value=True, key="use_adj",
              help="Divides closes before 2018-05-31 (TCS) and 2015-06-15 (Infosys) by 2.")
    st.number_input("Fast moving average (days)", 5, 100, 20, key="fast")
    st.number_input("Slow moving average (days)", 10, 250, 50, key="slow")
    if st.session_state["fast"] >= st.session_state["slow"]:
        st.error("Fast MA must be shorter than slow MA.")
        st.stop()

pg.run()