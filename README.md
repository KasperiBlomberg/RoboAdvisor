# Global Multi-asset Robo Advisor

[**Launch Live App**](https://globalroboadvisor.streamlit.app/)

A portfolio optimization engine that uses Modern Portfolio Theory (Markowitz Mean-Variance Optimization).

## Overview

This application calculates optimal asset weights based on risk tolerance and constraints. It solves for the efficient frontier using two different data models:
1.  **Institutional Consensus:** Forward-looking return estimates (J.P. Morgan 2026 Long-Term Capital Market Assumptions).
2.  **Historical Data:** Standard CAPM implementation using trailing market data.

## Features

* **Optimization Solver:** Convex optimization using `PyPortfolioOpt`.
* **Custom Constraints:** Dynamic weight caps to force diversification (e.g., max 25% per asset).
* **Data Pipeline:** ETL script fetches data daily from Yahoo Finance and stores it in PostgreSQL (Neon).
* **Visualization:** Interactive portfolio piechart and correlation matrix using Plotly.

## Setup

1.  **Clone and Install**
    ```bash
    git clone [https://github.com/KasperiBlomberg/RoboAdvisor.git](https://github.com/KasperiBlomberg/RoboAdvisor.git)
    pip install -r requirements.txt
    ```

2.  **Fetch Data**
    ```bash
    python etl.py
    ```

3.  **Run App**
    ```bash
    streamlit run app.py
    ```

## Disclaimer

**Educational use only.** This software uses mathematical models that may not predict future performance. I am not a financial advisor.

## License

MIT License.
