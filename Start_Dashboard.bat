@echo off
title AutoPulse AI - Realtime Social Intelligence Dashboard
cd /d "%~dp0"
echo =======================================================
echo   Starting AutoPulse AI Dashboard (Local: http://localhost:8501)
echo =======================================================
call .\venv\Scripts\activate
streamlit run dashboard.py
pause
