import yfinance as yf
import pandas as pd
from bcb import sgs
import streamlit as st

def get_macro_indicators():
    """
    Busca Selic e IPCA atualizados do BCB. 
    Possui fallback silencioso caso o site esteja fora ou sem internet.
    """
    try:
        # 432: Meta Selic, 13522: IPCA acumulado 12 meses
        selic_meta = sgs.get({'selic': 432}, last=1)
        ipca_12m = sgs.get({'ipca_12m': 13522}, last=1)

        return {
            'selic': float(selic_meta['selic'].iloc[-1]),
            'ipca': float(ipca_12m['ipca_12m'].iloc[-1])
        }
    except Exception:
        # Fallback silencioso (Valores médios históricos se offline)
        return {'selic': 11.25, 'ipca': 4.50} 

@st.cache_data(ttl=3600)
def get_asset_info(ticker):
    """
    Busca informações básicas de um ativo via Yahoo Finance.
    Cache de 1 hora para evitar excesso de requisições.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        # .info can be very slow as it fetches a lot of metadata.
        # We try to get only what we need.
        info = ticker_obj.info
        
        data = {
            'symbol': ticker,
            'name': info.get('longName', ticker),
            'price': info.get('currentPrice', info.get('regularMarketPrice', 0.0)),
            'sector': info.get('sector', 'Unknown'),
            'pe_ratio': info.get('forwardPE', info.get('trailingPE')),
            'roe': info.get('returnOnEquity'),
            'dividend_yield': info.get('dividendYield'),
            'beta': info.get('beta'),
            'market_cap': info.get('marketCap')
        }
        return data
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_batch_asset_data(tickers):
    """
    Busca dados para uma lista de ativos e retorna um DataFrame.
    """
    data_list = []
    for t in tickers:
        info = get_asset_info(t)
        if info:
            data_list.append(info)
    return pd.DataFrame(data_list)
