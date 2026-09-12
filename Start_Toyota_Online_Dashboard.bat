@echo off
title AutoPulse AI - Toyota Online Public Dashboard Launcher
cd /d "%~dp0"
echo =======================================================
echo   Launching Toyota Campaign Realtime Online Dashboard
echo =======================================================

call .\venv\Scripts\activate

:: Start Streamlit in the background on port 8502
start /B .\venv\Scripts\streamlit.exe run toyota_dashboard.py --server.headless true --server.port 8502

:: Give it 3 seconds to boot up
timeout /t 3 /nobreak > nul

:: Run Cloudflare Tunnel to generate public HTTPS link
python share_online.py 8502

pause
