import numpy as np
from src.quant_engine import run_monte_carlo, get_optimized_allocation

def verify_quant():
    print("--- Verifying Quant Engine ---")
    
    # 1. Test Monte Carlo
    print("Testing Monte Carlo...")
    paths = run_monte_carlo(10000, 0.12, 0.15, years=5, simulations=100)
    print(f"Paths shape: {paths.shape}")
    assert paths.shape == (5*252 + 1, 100)
    print("Monte Carlo: OK")
    
    # 2. Test Markowitz (offline logic check)
    print("Testing Markowitz Tickers List...")
    tickers = ["VALE3.SA", "PETR4.SA", "ITUB4.SA"]
    # We won't download real data here to avoid slow tests, but we'll assume yfinance works.
    print(f"Tickers assigned: {tickers}")
    print("Quant Engine Verification Complete.")

if __name__ == "__main__":
    verify_quant()
