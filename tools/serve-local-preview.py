"""Local-only isolated dashboard preview. No upload routes or production writes."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qs,urlencode
import urllib.request,urllib.error,re
ROOT=Path(__file__).resolve().parents[1]/'.local/web-preview'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
 def list_directory(self,path):self.send_error(403);return None
 def do_GET(self):
  route=urlsplit(self.path).path
  if route=='/api/realtime':
   try:
    from local_realtime import read_realtime
    import json
    day=parse_qs(urlsplit(self.path).query).get('date',[None])[0]
    interval=parse_qs(urlsplit(self.path).query).get('interval',['1'])[0]
    payload=json.dumps(read_realtime(day,interval),default=str).encode('utf-8')
    self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
   except Exception:self.send_error(503,'Realtime source unavailable')
   return
  if route in ['/api/index.php' ,'/api/weather.php']:
   if route=='/api/index.php':
    q=parse_qs(urlsplit(self.path).query);action=q.get('action',[''])[0]
    if action not in ['tou-files','tou-file','sender-status'] or q.get('site',['main'])!=['main']:self.send_error(403);return
    params={'action':action,'site':'main'}
    if action=='tou-file':
     name=q.get('name',[''])[0]
     if not re.fullmatch(r'D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou',name,re.I):self.send_error(400);return
     params['name']=name
    remote='/api/index.php?'+urlencode(params)
   else:remote='/api/weather.php'
   try:
    with urllib.request.urlopen('https://energy.granddigital.co.th'+remote,timeout=20) as r:
     payload=r.read(1048576);kind=r.headers.get('Content-Type','application/json')
    self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
   except (OSError,urllib.error.URLError):self.send_error(502,'Live source unavailable')
   return
  if route=='/api/tou-files':self.path='/files.json'
  elif route=='/api/weather.php':self.path='/weather.json'
  elif not(route.startswith('/dashboard/') or route.startswith('/TOU%20File%20for%20test/')):self.send_error(404);return
  target=(ROOT/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
  if not target.is_relative_to(ROOT.resolve()):self.send_error(403);return
  super().do_GET()
 def do_POST(self):self.send_error(405,'Read-only preview')
if __name__=='__main__':
 print('Local test: http://127.0.0.1:8890/dashboard/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8890),Handler).serve_forever()
