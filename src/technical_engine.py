import pandas as pd
import pandas_ta as ta
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=3600)
def get_technical_signals(ticker):
    """
    Analyzes RSI and EMA to provide a 'Timing' signal.
    """
    try:
        # Fetch last 3 months to calculate indicators
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            return "N/A"
        
        # Flatten MultiIndex columns if necessary
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if 'Close' not in df.columns:
            return "N/A"
        
        # Calculate RSI (14)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # Calculate EMA (50)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        
        if df['RSI'].dropna().empty or df['EMA50'].dropna().empty:
            return "N/A"
            
        last_close = df['Close'].dropna().iloc[-1]
        last_rsi = df['RSI'].dropna().iloc[-1]
        last_ema50 = df['EMA50'].dropna().iloc[-1]
        
        # Logic: 
        # Overbought: RSI > 70
        # Oversold: RSI < 30
        # Bullish Trend: Price > EMA50
        
        if last_rsi < 35:
            return "🔥 COMPRA (Sobrevendido)"
        elif last_rsi > 70:
            return "⚠️ ALTO (Sobrecomprado)"
        elif last_close > last_ema50:
            return "✅ TENDRÊNCIA ALTA"
        else:
            return "⚖️ NEUTRO / QUEDA"
            
    except Exception as e:
        return "Erro"
