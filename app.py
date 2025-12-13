import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from pypfopt import EfficientFrontier, risk_models, expected_returns

# Page configuration
st.set_page_config(page_title="Robo Advisor", page_icon="🤖", layout="centered")

# Header
col_header, col_logo = st.columns([9, 1])
with col_header:
    st.markdown("**Global Multi-Asset Portfolio Optimizer**")

# Database connection
def get_db_engine():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url)

@st.cache_data(ttl=3600, show_spinner=False)
def get_market_data():
    engine = get_db_engine()
    
    query = "SELECT * FROM stock_prices"
    
    with engine.connect() as conn:
        df_long = pd.read_sql(query, conn)
    
    # Pivot to wide for math
    df_wide = df_long.pivot(index="Date", columns="Ticker", values="Price")
    df_wide.index = pd.to_datetime(df_wide.index)
    
    return df_wide


# Load Data
try:
    with st.spinner("Initializing market data feed..."):
        df = get_market_data()
except Exception as e:
    st.error("Connection to Database Failed")
    with st.expander("Technical Error Log"):
        st.code(str(e))
    st.stop()

# Sidebar
with st.sidebar:
    st.header("Client Profile")

    # Investment amount
    investment = st.number_input(
        "Investment Amount ($)", min_value=1000, value=10000, step=1000, format="%d"
    )

    # Risk tolerance
    risk_level = st.slider(
        "Risk Tolerance (1-10)",
        min_value=1,
        max_value=10,
        value=6,
        help="1 = Conservative (Bonds), 10 = Aggressive (Stocks)",
    )

    st.markdown("---")
    st.header("Strategy Settings")

    # Return model selection
    model_choice = st.selectbox(
        "Expected Return Model",
        ["Institutional Consensus (J.P. Morgan 2026)", "Historical Data (CAPM)"],
        help="Institutional uses forward-looking forecasts. Historical uses past performance.",
    )

    # Diversification constraint
    max_alloc = st.slider(
        "Max Allocation per Asset",
        min_value=0.15,
        max_value=1.00,
        value=0.25,
        step=0.05,
        format="%.2f",
        help="Diversification Rule: No single asset can exceed this weight.",
    )


# Dashboard
tab1, tab2 = st.tabs(["Strategy Dashboard", "Market Data Inspector"])

# Tab 1 portfolio optimization
with tab1:
    st.subheader("Strategic Asset Allocation")

    # Define expected returns
    if model_choice == "Institutional Consensus (J.P. Morgan 2026)":
        # 2026 Arithmetic Returns (from LTCMA)
        mu_raw = {
            "SPY": 0.0794,
            "QQQ": 0.0834,
            "IWM": 0.0889,
            "VGK": 0.0994,
            "EEM": 0.0974,
            "IEI": 0.0406,
            "HYG": 0.0646,
            "GLD": 0.0678,
            "VNQ": 0.0879,
        }
        mu = pd.Series(mu_raw)
    else:
        mu = expected_returns.capm_return(df)

    # Optimization engine
    mu = mu.reindex(df.columns).fillna(0.0)
    S = risk_models.CovarianceShrinkage(df).ledoit_wolf()

    # Map 1-10 Slider to Volatility Target (5% to 25%)
    min_vol = 0.05
    max_vol = 0.25

    target_vol = min_vol + (max_vol - min_vol) * (risk_level - 1) / 9

    # Calculate Optimal Weights
    try:
        ef = EfficientFrontier(mu, S, weight_bounds=(0.01, max_alloc))
        weights = ef.efficient_risk(target_vol)

    except:
        st.warning(
            f"Risk Target {target_vol:.1%} unreachable with these constraints. Defaulting to Max Sharpe."
        )
        # Re-initialize so it doesn't crash
        ef = EfficientFrontier(mu, S, weight_bounds=(0.01, max_alloc))
        weights = ef.max_sharpe()

    cleaned_weights = ef.clean_weights()

    # Visualization
    ticker_map = {
        "SPY": "US Large Cap (S&P 500)",
        "QQQ": "US Tech (Nasdaq)",
        "IWM": "US Small Cap (Russell 2000)",
        "VGK": "Developed Europe",
        "EEM": "Emerging Markets",
        "IEI": "Govt Bonds (Safe)",
        "HYG": "Corp Bonds (High Yield)",
        "GLD": "Gold",
        "VNQ": "Real Estate",
    }

    color_map = {
        "US Large Cap (S&P 500)": "#1f77b4",
        "US Tech (Nasdaq)": "#00bfff",
        "US Small Cap (Russell 2000)": "#8c564b",
        "Developed Europe": "#2ca02c",
        "Emerging Markets": "#ff7f0e",
        "Govt Bonds (Safe)": "#7f7f7f",
        "Corp Bonds (High Yield)": "#e377c2",
        "Gold": "#bcbd22",
        "Real Estate": "#9467bd",
    }

    # Display
    col_charts, col_metrics = st.columns([2, 1])

    with col_charts:
        # Pie Chart
        weights_df = pd.Series(cleaned_weights).reset_index()
        weights_df.columns = ["Asset Code", "Weight"]
        weights_df["Asset Name"] = weights_df["Asset Code"].map(ticker_map)

        # Filter out zero weights for cleaner chart
        weights_df = weights_df[weights_df["Weight"] >= 0.01]

        fig_pie = px.pie(
            weights_df,
            values="Weight",
            names="Asset Name",
            color="Asset Name",
            color_discrete_map=color_map,
            hole=0.4,
        )
        fig_pie.update_layout(showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_metrics:
        # Portfolio Stats
        st.markdown("#### Projected Performance")
        perf = ef.portfolio_performance(verbose=False, risk_free_rate=0.04)

        st.metric("Expected Annual Return", f"{perf[0]*100:.1f}%")
        st.metric("Annual Volatility (Risk)", f"{perf[1]*100:.1f}%")
        st.metric("Sharpe Ratio", f"{perf[2]:.2f}")

    # Correlation Matrix
    st.markdown("---")
    st.subheader("Asset Correlation Matrix")
    st.caption(
        "Dark Red = High Correlation (Assets move together). Blue = Low Correlation (Diversifiers)."
    )

    corr_matrix = df.pct_change().corr()
    corr_viz = corr_matrix.rename(index=ticker_map, columns=ticker_map)

    fig_corr = px.imshow(
        corr_viz,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        origin="lower",
    )
    st.plotly_chart(fig_corr, use_container_width=True)


# Tab 2
with tab2:
    st.header("Market Data")

    # Metadata Metrics
    latest_date = df.index.max().strftime("%Y-%m-%d")
    earliest_date = df.index.min().strftime("%Y-%m-%d")
    total_days = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Data Point", latest_date)
    col2.metric("History Depth", f"{earliest_date} to Present")
    col3.metric("Total Trading Days", total_days)

    st.markdown("---")

    # Recent Price Data
    st.subheader("Raw Price Data (USD)")
    st.dataframe(
        df.tail(10).sort_index(ascending=False).style.format("{:.2f}"),
        use_container_width=True,
    )

    # Export Button
    st.download_button(
        label="📥 Download Dataset (.csv)",
        data=df.to_csv().encode("utf-8"),
        file_name="meridian_market_data.csv",
        mime="text/csv",
    )
