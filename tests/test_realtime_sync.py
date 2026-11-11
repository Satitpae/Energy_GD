import sys,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'uploader'),str(ROOT/'.cache/mysql-client')]
import realtime_sync as sync
class Response:
 def __init__(self,req,bad=False):self.req=req;self.bad=bad
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,n):
  from urllib.parse import urlsplit,parse_qs
  q=parse_qs(urlsplit(self.req.full_url).query)
  return json.dumps({'ok':not self.bad,'date':q['date'][0],'interval':int(q['interval'][0])}).encode()
class SyncTests(unittest.TestCase):
 def test_disabled(self):self.assertEqual(sync.sync_once({},'unused'),{'realtime_sent':0})
 def test_acknowledged_history_and_no_credentials(self):
  from datetime import datetime,timezone,timedelta
  today=datetime.now(timezone(timedelta(hours=7))).date();yesterday=today-timedelta(days=1)
  config={'base_url':'https://example.test','upload_token':'private-token','realtime':{'enabled':True,'mysql':{'password':'private-db-password'},'history_start':str(yesterday)}}
  class Opener:
   def open(self,req,timeout):
    import gzip
    assert b'private-db-password' not in gzip.decompress(req.data)
    return Response(req)
  with tempfile.TemporaryDirectory(dir=ROOT/".local")as d,patch.object(sync,'read_realtime',return_value={'ok':True}),patch.object(sync.urllib.request,'build_opener',return_value=Opener()):
   path=Path(d)/'state.json';self.assertEqual(sync.sync_once(config,path)['realtime_sent'],10)
   self.assertEqual(json.loads(path.read_text())['cursor'],str(yesterday-timedelta(days=1)))
   self.assertEqual(sync.sync_once(config,path)['realtime_sent'],5)
 def test_failure_does_not_advance_cursor(self):
  config={'base_url':'https://example.test','upload_token':'x','realtime':{'enabled':True,'mysql':{},'history_start':'2026-11-01'}}
  class Opener:
   def open(self,req,timeout):return Response(req,True)
  with tempfile.TemporaryDirectory(dir=ROOT/".local")as d,patch.object(sync,'read_realtime',return_value={'ok':True}),patch.object(sync.urllib.request,'build_opener',return_value=Opener()):
   path=Path(d)/'state.json'
   with self.assertRaises(ValueError):sync.sync_once(config,path)
   self.assertFalse(path.exists())
if __name__=='__main__':unittest.main()

