import pandas as pd
from pypfopt import EfficientFrontier, risk_models, expected_returns
from src.config import JPM_2026_RETURN_FORECASTS, RISK_FREE_RATE

def calculate_metrics(df, model_choice):
    """Calculates Mu (Returns) and S (Covariance)."""
    
    S = risk_models.CovarianceShrinkage(df).ledoit_wolf()

    if model_choice == "Institutional Consensus (J.P. Morgan 2026)":
        mu = pd.Series(JPM_2026_RETURN_FORECASTS)
    else:
        # CAPM (Historical)
        mu = expected_returns.capm_return(df, risk_free_rate=RISK_FREE_RATE)
    
    # Ensure dimensions match
    mu = mu.reindex(df.columns).fillna(0.0)
    
    return mu, S

def run_optimization(mu, S, risk_tolerance_score, max_alloc):
    """
    Runs Mean-Variance Optimization.
    risk_tolerance_score: 1 (Conservative) to 10 (Aggressive)
    """
    
    # Map 1-10 Score to Volatility Target (5% to 25%)
    min_vol = 0.05
    max_vol = 0.25
    target_vol = min_vol + (max_vol - min_vol) * (risk_tolerance_score - 1) / 9

    # Initialize Efficient Frontier
    ef = EfficientFrontier(mu, S, weight_bounds=(0.0, max_alloc))
    
    try:
        # Maximize return for given volatility
        ef.efficient_risk(target_vol)
    except:
        # Fallback to Max Sharpe if target is unreachable
        print("Target volatility unreachable. Defaulting to Max Sharpe.")
        ef = EfficientFrontier(mu, S, weight_bounds=(0.0, max_alloc))
        ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
        
    cleaned_weights = ef.clean_weights()
    performance = ef.portfolio_performance(verbose=False, risk_free_rate=RISK_FREE_RATE)
    
    return cleaned_weights, performance