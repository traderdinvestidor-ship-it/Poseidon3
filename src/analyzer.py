import pandas as pd

def score_stocks(df):
    """
    Scores stocks based on Graham/Greenblatt logic (simplified).
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Filter cleanup
    df = df.dropna(subset=['roe', 'pe_ratio'])
    
    # Basic Filters
    df = df[df['roe'] > 0.10] # ROE > 10%
    df = df[df['pe_ratio'] > 0] # Profitable
    
    # Scoring: Rank by Cheapest (Low P/E) + Best Quality (High ROE)
    df['rank_pe'] = df['pe_ratio'].rank(ascending=True)
    df['rank_roe'] = df['roe'].rank(ascending=False)
    df['score'] = df['rank_pe'] + df['rank_roe']
    
    return df.sort_values('score').head(10) # Top 10 Best

def score_crypto(df):
    """
    Score crypto mainly by market cap (Safety).
    """
    if df.empty:
        return df
    
    df = df.copy()
    return df.sort_values('market_cap', ascending=False)
