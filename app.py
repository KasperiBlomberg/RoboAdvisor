import streamlit as st
import pandas as pd
import plotly.express as px
from src.data import get_market_data
from src.optimization import calculate_metrics, run_optimization
from src.config import TICKER_MAP, COLOR_MAP

# Page Config
st.set_page_config(page_title="Robo Advisor", page_icon="🤖", layout="centered")

# --- HEADER ---
col_header, col_logo = st.columns([9, 1])
with col_header:
    st.markdown("**Global Multi-Asset Portfolio Optimizer**")

# --- DATA LOADING ---
try:
    with st.spinner("Initializing market data feed..."):
        df = get_market_data()
except Exception as e:
    st.error("Database Connection Failed")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Client Profile")
    investment = st.number_input("Investment Amount (€)", value=10000, step=1000)

    risk_level = st.slider(
        "Risk Tolerance (1-10)",
        1,
        10,
        6,
        help="1 = Conservative (Bonds), 10 = Aggressive (Stocks)",
    )

    st.markdown("---")
    st.header("Strategy Settings")

    model_choice = st.selectbox(
        "Expected Return Model",
        ["Institutional Consensus (J.P. Morgan 2026)", "Historical Data (CAPM)"],
    )

    max_alloc = st.slider("Max Asset Allocation", 0.15, 1.00, 0.25, 0.05)

    with st.expander("ℹ️ Currency Assumptions"):
        st.caption("Model assumes FX Neutrality (Uncovered Interest Parity).")

# --- MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["Strategy Dashboard", "Market Data Inspector"])

with tab1:
    st.subheader("Strategic Asset Allocation")

    # RUN OPTIMIZATION
    mu, S = calculate_metrics(df, model_choice)
    weights, perf = run_optimization(mu, S, risk_level, max_alloc)

    # VISUALIZATION
    col_charts, col_metrics = st.columns([2, 1])

    with col_charts:
        # Prepare Data for Pie Chart
        weights_df = pd.Series(weights).reset_index()
        weights_df.columns = ["Ticker", "Weight"]
        weights_df["Name"] = weights_df["Ticker"].map(TICKER_MAP)

        # Filter small weights
        weights_df = weights_df[weights_df["Weight"] >= 0.01]

        fig_pie = px.pie(
            weights_df,
            values="Weight",
            names="Name",
            color="Name",
            color_discrete_map=COLOR_MAP,
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_metrics:
        st.markdown("#### Projected Performance")
        st.metric("Expected Return", f"{perf[0]*100:.1f}%")
        st.metric("Annual Volatility", f"{perf[1]*100:.1f}%")
        st.metric("Sharpe Ratio", f"{perf[2]:.2f}")

    # CORRELATION MATRIX
    st.markdown("---")
    st.subheader("Asset Correlation Matrix")
    st.caption(
        "Dark Red = High Correlation (Assets move together). Blue = Low Correlation (Diversifiers)."
    )

    corr_matrix = df.pct_change().corr()

    corr_viz = corr_matrix.rename(index=TICKER_MAP, columns=TICKER_MAP)

    fig_corr = px.imshow(
        corr_viz,
        text_auto=".2f",
        aspect="equal",
        color_continuous_scale="RdBu_r",
        origin="lower",
    )

    fig_corr.update_layout(
        height=700,
        xaxis=dict(
            tickangle=-45,
            side="bottom",
        ),
        yaxis=dict(tickmode="linear"),
        margin=dict(t=50, b=100),
    )

    st.plotly_chart(fig_corr, use_container_width=True)

with tab2:
    st.header("Market Data Inspector")

    # --- METADATA METRICS ---
    # Check if dataframe is not empty to avoid errors
    if not df.empty:
        latest_date = df.index.max().strftime("%Y-%m-%d")
        earliest_date = df.index.min().strftime("%Y-%m-%d")
        total_days = len(df)

        # Display Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Latest Data Point", latest_date)
        col2.metric("History Start", earliest_date)
        col3.metric("Total Trading Days", total_days)

    st.markdown("---")

    # --- RAW DATA TABLE ---
    st.subheader("Raw Price Data (EUR)")
    st.caption("Post-processing data fed into the optimizer.")

    # Show last 10 rows, sorted newest first
    st.dataframe(
        df.tail(10).sort_index(ascending=False).style.format("{:.2f}"),
        use_container_width=True,
    )

    # --- DOWNLOAD BUTTON ---
    csv_data = df.to_csv().encode("utf-8")
    st.download_button(
        label="📥 Download Dataset (.csv)",
        data=csv_data,
        file_name="robo_advisor_data.csv",
        mime="text/csv",
    )
