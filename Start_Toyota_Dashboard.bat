@echo off
title AutoPulse AI - Toyota Campaign Intelligence Dashboard
cd /d "%~dp0"
echo =======================================================
echo   Starting Toyota Campaign Dashboard (Local: http://localhost:8502)
echo =======================================================
call .\venv\Scripts\activate
streamlit run toyota_dashboard.py --server.port 8502
pause
