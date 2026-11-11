"""Create a read-only production snapshot in an isolated local preview folder."""
import json,urllib.request,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'.local/web-preview'
BASE='https://energy.granddigital.co.th'
def fetch(path):
 with urllib.request.urlopen(BASE+path,timeout=30) as r:return r.read()
def main():
 (DEST/'dashboard').mkdir(parents=True,exist_ok=True)
 (DEST/'TOU File for test').mkdir(exist_ok=True)
 assets=['index.html','style.css','combined-app.js','combined.mjs','parser.mjs','tou.mjs','excel.mjs','sender-status.mjs','demand-window.mjs','weather.js','company-logo.png']
 for name in assets:(DEST/'dashboard'/name).write_bytes(fetch('/dashboard/'+name))
 (DEST/'dashboard/mode.js').write_text('window.EMS_ONLINE=false;window.EMS_PUBLIC_READ=false;',encoding='utf-8')
 p=DEST/'dashboard/index.html';s=p.read_text(encoding='utf-8');s=s.replace('<body>','<body><div style="padding:10px 20px;background:#fff0d9;color:#8b4d12;text-align:center;font:14px Tahoma">ทดสอบในเครื่อง · ข้อมูลสำเนา · ไม่ส่งข้อมูลหรือแก้ไขเว็บจริง</div>');p.write_text(s,encoding='utf-8')
 manifest=json.loads(fetch('/api/index.php?action=tou-files&site=main'))
 import re,urllib.parse
 files=[f for f in manifest['files'] if re.fullmatch(r'D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou',f['name'],re.I)]
 def download(f):
  name=f['name'];(DEST/'TOU File for test'/name).write_bytes(fetch('/api/index.php?action=tou-file&site=main&name='+urllib.parse.quote(name)))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,files))
 (DEST/'files.json').write_text(json.dumps({'files':files}),encoding='utf-8')
 (DEST/'weather.json').write_bytes(fetch('/api/weather.php'))
 print('Local snapshot ready:',len(files),'files. No production writes or credentials used.')
if __name__=='__main__':main()
