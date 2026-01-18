import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

def get_db_engine():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url)

@st.cache_data(ttl=3600, show_spinner=False)
def get_market_data():
    """Fetches and pivots data from Postgres."""
    engine = get_db_engine()
    query = "SELECT * FROM stock_prices"

    with engine.connect() as conn:
        df_long = pd.read_sql(query, conn)

    # Pivot to wide format (Date x Ticker)
    df_wide = df_long.pivot(index="Date", columns="Ticker", values="Price")
    df_wide.index = pd.to_datetime(df_wide.index)
    
    # Sort to ensure latest data is last
    df_wide = df_wide.sort_index()

    return df_wide