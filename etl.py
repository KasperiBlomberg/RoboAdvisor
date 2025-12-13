import os
import yfinance as yf
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Configuration
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
TICKERS = ["SPY", "QQQ", "IWM", "VGK", "EEM", "IEI", "HYG", "GLD", "VNQ"]
START_DATE = "2015-01-01"


def extract_data():
    """EXTRACT: Fetch raw data from API."""
    print(f"Extraction: Fetching data for {len(TICKERS)} tickers...")
    data = yf.download(TICKERS, start=START_DATE)["Close"]
    return data


def transform_data(df):
    """TRANSFORM: Clean and normalize data."""
    print("Transformation: Aligning timeframes...")

    # Find the common start date by dropping missing rows
    df_aligned = df.dropna()

    print(
        f"-> Data start date moved to {df_aligned.index[0].date()} to match the youngest asset."
    )

    # 2. Reshape for Database
    df_long = df_aligned.reset_index().melt(
        id_vars=["Date"], var_name="Ticker", value_name="Price"
    )
    return df_long


def load_data(df):
    engine = create_engine(DATABASE_URL)
    try:
        df.to_sql('stock_prices', engine, if_exists='replace', index=True)
        print(f"Success! {len(df)} rows uploaded to Neon Postgres.")
    except Exception as e:
        print(f"Upload Failed: {e}")


if __name__ == "__main__":
    raw_data = extract_data()
    clean_data = transform_data(raw_data)
    load_data(clean_data)
