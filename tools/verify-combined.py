"""Read-only production checks for the combined dashboard; never upload fixtures."""
import json, urllib.request, urllib.error
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base='https://energy.granddigital.co.th'
for name in ['index.html','style.css','combined.mjs','combined-app.js','sender-status.mjs']:
 with urllib.request.urlopen(base+'/dashboard/'+name,timeout=20) as r:
  text=r.read().decode().replace('\r','')
  assert text==(root/'dashboard'/name).read_text(encoding='utf-8').replace('\r',''),name
  if name.endswith(('.mjs','.js')):assert 'javascript' in r.headers.get('Content-Type','')
with urllib.request.urlopen(base+'/api/index.php?action=tou-files&site=main',timeout=20) as r:
 files=json.load(r)['files']
assert len(files)>=126
try:
 urllib.request.urlopen(urllib.request.Request(base+'/api/index.php?action=upload&site=main&name=D01Oct26.tou',data=b'no',headers={'Content-Type':'application/octet-stream'}),timeout=20)
 raise AssertionError('Anonymous upload accepted')
except urllib.error.HTTPError as e:assert e.code==401
print('Combined assets match; public files:',len(files),'; anonymous upload denied. No source/data files changed.')
