@echo off
cd /d "%~dp0"
python launch.py stop --config config.neverdie.local.json
pause
