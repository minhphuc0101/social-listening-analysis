@echo off
title AutoPulse AI - Online Public Dashboard Launcher
cd /d "%~dp0"
echo =======================================================
echo   Launching AutoPulse AI Realtime Online Dashboard
echo =======================================================

call .\venv\Scripts\activate

:: Start Streamlit in the background if not already running
start /B .\venv\Scripts\streamlit.exe run dashboard.py --server.headless true --server.port 8501

:: Give it 3 seconds to boot up
timeout /t 3 /nobreak > nul

:: Run Cloudflare Tunnel to generate public HTTPS link
python share_online.py 8501

pause
