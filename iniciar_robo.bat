@echo off
title Poseidon Investimentos - Iniciando...
echo ====================================================
echo           POSEIDON INVESTIMENTOS - LAUNCHER
echo ====================================================
echo.
echo [1/2] Entrando no diretorio do projeto...
cd /d "%~dp0"
echo [2/2] Iniciando o Dashboard Streamlit...
echo.
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m streamlit run app.py
pause
