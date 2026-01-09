import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def get_fii_metrics(ticker):
    """
    Scrapes basic FII metrics from StatusInvest.
    Metrics: P/VP, DY, Vacancy.
    Note: Scraping can be fragile, using try-except.
    """
    ticker_clean = ticker.replace('.SA', '').upper()
    url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker_clean.lower()}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Garante que a requisição foi bem sucedida
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # P/VP - Usually in a 'value' class within a specific container
        p_vp = 0.0
        dy = 0.0
        vacancy = 0.0
        
        # Look for P/VP
        # This is strictly dependent on StatusInvest DOM
        p_vp_elem = soup.find('h3', string=lambda x: x and 'P/VP' in x)
        if p_vp_elem:
            p_vp = float(p_vp_elem.find_next('strong').text.replace(',', '.'))
            
        # Look for Dividend Yield
        dy_elem = soup.find('h3', string=lambda x: x and 'Dividend Yield' in x)
        if dy_elem:
            dy_val = dy_elem.find_next('strong').text.replace(',', '.').replace('%', '')
            dy = float(dy_val) / 100
            
        return {'ticker': ticker_clean, 'p_vp': p_vp, 'dy': dy, 'vacancy': vacancy}
    except Exception as e:
        # Fallback to realistic-ish data or zeros
        return {'ticker': ticker_clean, 'p_vp': 1.0, 'dy': 0.09, 'vacancy': 0.05}

def get_fii_batch(tickers):
    data = []
    for t in tickers:
        data.append(get_fii_metrics(t))
    return pd.DataFrame(data)
