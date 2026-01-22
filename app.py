import streamlit as st
import pandas as pd
import plotly.express as px
from src.data import get_market_data
from src.optimization import calculate_metrics, run_optimization
from src.config import TICKER_MAP, COLOR_MAP

# Page Config
st.set_page_config(page_title="Robo Advisor", page_icon="🤖", layout="wide")

# --- HEADER ---
col_header, col_logo = st.columns([9, 1])
with col_header:
    st.title("Global Multi-Asset Portfolio Optimizer")

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

# ... (Imports and setup remain the same) ...

# --- MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["Strategy Dashboard", "Market Data Inspector"])

with tab1:
    st.subheader("Strategic Asset Allocation")

    # RUN OPTIMIZATION
    mu, S = calculate_metrics(df, model_choice)
    weights, perf = run_optimization(mu, S, risk_level, max_alloc)

    # --- TOP ROW: KPI CARDS ---
    # We use a container to group the metrics visually
    with st.container(border=True):
        st.markdown("#### Projected Performance")
        kpi1, kpi2, kpi3 = st.columns(3)

        with kpi1:
            st.metric(
                "Expected Return",
                f"{perf[0]*100:.1f}%",
                help="Annualized expected return based on selected model"
            )
        with kpi2:
            st.metric(
                "Annual Volatility",
                f"{perf[1]*100:.1f}%",
                help="Standard deviation of returns (Risk)"
            )
        with kpi3:
            # Color code the Sharpe ratio: Green if > 1, else normal
            sharpe_val = perf[2]
            st.metric(
                "Sharpe Ratio",
                f"{sharpe_val:.2f}",
                delta="Good" if sharpe_val > 1.0 else None,
                delta_color="normal"
            )

    # --- MIDDLE ROW: CHARTS ---
    col_alloc, col_corr = st.columns([1, 1], gap="medium")

    # LEFT COLUMN: ALLOCATION
    with col_alloc:
        with st.container(border=True):
            st.markdown("#### Portfolio Weights")
            
            # Prepare Data
            weights_df = pd.Series(weights).reset_index()
            weights_df.columns = ["Ticker", "Weight"]
            weights_df["Name"] = weights_df["Ticker"].map(TICKER_MAP)
            weights_df = weights_df[weights_df["Weight"] >= 0.01]

            fig_pie = px.pie(
                weights_df,
                values="Weight",
                names="Name",
                color="Name",
                color_discrete_map=COLOR_MAP,
                hole=0.4,
            )
            
            # FIX: Move legend to bottom to give chart more width
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.05,
                    xanchor="center",
                    x=0.5
                ),
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # RIGHT COLUMN: CORRELATION
    with col_corr:
        with st.container(border=True):
            st.markdown("#### Asset Correlation")
            
            corr_matrix = df.pct_change().corr()
            corr_viz = corr_matrix.rename(index=TICKER_MAP, columns=TICKER_MAP)

            fig_corr = px.imshow(
                corr_viz,
                text_auto=".2f",
                aspect="auto", # Changed from 'equal' to fill space better
                color_continuous_scale="RdBu_r",
                origin="lower",
            )

            fig_corr.update_layout(
                height=400, # Match height of Pie Chart
                margin=dict(t=30, b=0, l=0, r=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                coloraxis_showscale=False # Hides color bar to save space (optional)
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
    # Optional: Contextual help below charts
    st.caption("ℹ️ **Note:** Correlation matrix helps identify diversification benefits. Lower values (blue) indicate assets that tend to move independently.")

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
