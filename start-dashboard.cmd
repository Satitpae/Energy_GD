@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Open http://127.0.0.1:8766/dashboard/
echo Keep this window open while using the dashboard. Press Ctrl+C to stop.
python local_server.py
pause
