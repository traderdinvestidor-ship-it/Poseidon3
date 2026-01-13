import pandas as pd

def score_stocks(df):
    """
    Scores stocks based on Graham/Greenblatt logic (simplified).
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Garante que as colunas numéricas existam e preenche vazios com 0
    cols_to_fix = ['roe', 'pe_ratio', 'price']
    for col in cols_to_fix:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Filtro básico: Apenas remove se não tiver preço (dado inválido)
    df = df[df['price'] > 0.01] # Garante que o preço é maior que 1 centavo
    
    if df.empty:
        return df
    
    # Scoring: Rank by Cheapest (Low P/E) + Best Quality (High ROE)
    # Tratamento para P/L zero (evita que empresas sem lucro fiquem no topo)
    df['pe_clean'] = df['pe_ratio'].replace(0, 1000)
    
    df['rank_pe'] = df['pe_clean'].rank(ascending=True)
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
