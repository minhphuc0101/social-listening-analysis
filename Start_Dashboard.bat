@echo off
title AutoPulse AI - Realtime Social Intelligence Dashboard
cd /d "%~dp0"
echo =======================================================
echo   Starting AutoPulse AI Dashboard (Local: http://localhost:8501)
echo =======================================================

if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

streamlit run dashboard.py
pause
