"""Build a data-free portable Windows x64 executable."""
from pathlib import Path
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/satec-pq'
command=[sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed','--name','PQDashboard','--paths',str(SOURCE),'--distpath',str(ROOT/'releases/PQ-Dashboard-1.0.9'),'--workpath',str(ROOT/'.cache/pq-pyinstaller'),'--specpath',str(ROOT/'.cache')]
for name in ['template.html','base-style.css','tou-preview.js','app.js','wave-data.js','wave-interaction.js','live-refresh.js','extract-access.ps1','data_store.py','build_preview.py']:
    command+=['--add-data',str(SOURCE/name)+';.']
for name in ('template.html', 'core.mjs', 'app.js'):
    command += ['--add-data', str(ROOT / 'reports/advreports-events' / name) + ';flood-assets']
command += ['--add-data', str(ROOT / 'reports/pq-integrated-preview.html') + ';.']
command.append(str(SOURCE/'desktop_pq.py'))
environment=dict(os.environ);environment['PYINSTALLER_CONFIG_DIR']=str(ROOT/'.cache/pq-build-config')
subprocess.run(command,cwd=ROOT,env=environment,check=True)
