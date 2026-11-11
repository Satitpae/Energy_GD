@echo off
cd /d "%~dp0"
python launch.py status --config config.neverdie.local.json
pause
