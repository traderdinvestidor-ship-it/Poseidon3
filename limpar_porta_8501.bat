@echo off
echo Encerrando processos do Streamlit na porta 8501...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501') do taskkill /f /pid %%a
echo Limpeza concluida!
pause
