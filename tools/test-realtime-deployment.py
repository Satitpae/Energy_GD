"""Exercise actual PHP receiver locally with real read-only MySQL snapshots."""
import sys,json,gzip,subprocess,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'uploader'),str(ROOT/'.cache/mysql-client')]
from local_realtime import read_realtime
import shutil
base=ROOT/'.local/realtime-integration';web=base/'domains/energy/public_html';api=web/'api';api.mkdir(parents=True,exist_ok=True)
private=base/'.php/granddigital-ems-tou-private';private.mkdir(parents=True,exist_ok=True)
store=base/'data';store.mkdir(exist_ok=True)
(private/'config.php').write_text("<?php return ['upload_token'=>'local-integration-token','data_dir'=>"+repr(store.as_posix())+"];",encoding='utf-8')
shutil.copy2(ROOT/'neverdie/realtime.php',api/'realtime.php')
p=subprocess.Popen([str(ROOT/'.cache/php/php.exe'),'-S','127.0.0.1:8891','-t',str(web)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def request(interval,body=None,auth=True):
 req=urllib.request.Request('http://127.0.0.1:8891/api/realtime.php?date=2026-11-03&interval='+str(interval),data=body,headers={'Authorization':'Bearer local-integration-token'} if auth else {})
 try:
  with urllib.request.urlopen(req,timeout=10)as r:return r.status,json.loads(r.read())
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
try:
 time.sleep(1)
 assert request(1,b'bad',False)[0]==401
 assert request(1,gzip.compress(b'{}'))[0]==400
 for interval in [1,5,15,30,60]:
  d=read_realtime('2026-11-03',interval);payload=gzip.compress(json.dumps(d,default=str).encode())
  assert request(interval,payload)[0]==200
  status,got=request(interval)
  assert status==200 and got['interval_minutes']==interval
  assert len(got['devices'][0]['history'])==len(d['devices'][0]['history'])
  assert got['devices'][0]['latest']['kW']==d['devices'][0]['latest']['kW']
  assert 'datatbl_' not in json.dumps(got)
  print('PASS interval',interval,'rows',len(got['devices'][0]['history']))
 print('PASS unauthorized, invalid payload, all interval round trips, table names absent')
finally:p.terminate();p.wait(timeout=10)
