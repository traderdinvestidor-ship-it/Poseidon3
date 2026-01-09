import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

def run_monte_carlo(initial_capital, annual_return, annual_vol, years=10, simulations=1000):
    """
    Simulates portfolio growth using Geometric Brownian Motion.
    """
    dt = 1/252 # Daily steps
    trading_days = years * 252
    
    # Pre-calculate daily drift and vol
    mu = annual_return / 252
    sigma = annual_vol / np.sqrt(252)
    
    # Generate random shocks
    shocks = np.random.normal(mu, sigma, (trading_days, simulations))
    
    # Calculate price paths
    # Price_t = Price_{t-1} * exp(shock)
    path_returns = np.exp(shocks)
    paths = initial_capital * np.cumprod(path_returns, axis=0)
    
    # Add initial capital as the first row
    paths = np.vstack([np.full(simulations, initial_capital), paths])
    
    return paths

def get_optimized_allocation(tickers, risk_profile):
    """
    Calculates weights for the Max Sharpe Ratio portfolio using historical data.
    """
    try:
        # Fetch 2 years of history
        data = yf.download(tickers, period="2y", interval="1d", progress=False, auto_adjust=True)
        
        if data.empty or 'Close' not in data.columns or len(tickers) < 2:
            return None
            
        returns = data['Close'].pct_change().dropna()
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        num_assets = len(tickers)
        
        def portfolio_performance(weights, mean_returns, cov_matrix):
            returns = np.dot(weights, mean_returns)
            std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return returns, std
            
        # Target: Maximize Sharpe Ratio (Minimize -Sharpe)
        def negative_sharpe(weights, mean_returns, cov_matrix, risk_free_rate=0.1175):
            p_ret, p_std = portfolio_performance(weights, mean_returns, cov_matrix)
            return -(p_ret - risk_free_rate) / p_std
            
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0.05, 0.4) for _ in range(num_assets)) # Min 5%, Max 40% per asset for diversification
        initial_weights = [1./num_assets] * num_assets
        
        optimized = minimize(negative_sharpe, initial_weights, 
                             args=(mean_returns, cov_matrix),
                             method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not optimized.success:
            return None
            
        return dict(zip(tickers, optimized.x))
    except Exception:
        return None
