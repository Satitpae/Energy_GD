"""Upload read-only day snapshots; credentials never leave this computer."""
import gzip,json,urllib.request,urllib.parse
from datetime import datetime,timedelta,timezone
from pathlib import Path
from realtime_source import read_realtime

def sync_once(config,state_path,stop_requested=lambda:False):
 options=config.get('realtime',{})
 if not options.get('enabled'):return {'realtime_sent':0}
 from send import NoRedirect,write_state
 today=datetime.now(timezone(timedelta(hours=7))).date()
 path=Path(state_path)
 state=json.loads(path.read_text()) if path.exists() else {}
 # Recent days first, continuing further back after every successful acknowledgement.
 start=datetime.strptime(options.get('history_start','2026-11-01'),'%Y-%m-%d').date()
 cursor=datetime.strptime(state.get('cursor',str(today-timedelta(days=1))),'%Y-%m-%d').date()
 if state.get('cycle_day')!=str(today):
  cursor=today-timedelta(days=1);state['cycle_day']=str(today)
 days=[today]+([cursor] if start<=cursor<today else [])
 sent=0
 for day in days:
  for interval in [1,5,15,30,60]:
   if stop_requested():return {'realtime_sent':sent}
   payload=read_realtime(str(day),interval,options['mysql'])
   body=gzip.compress(json.dumps(payload,default=str,separators=(',',':')).encode(),mtime=0)
   query=urllib.parse.urlencode({'site':config.get('site','main'),'date':str(day),'interval':interval})
   url=config['base_url'].rstrip('/')+'/api/realtime.php?'+query
   if not url.startswith('https://'):raise ValueError('Realtime requires HTTPS')
   request=urllib.request.Request(url,data=body,method='POST',headers={'Authorization':'Bearer '+config['upload_token'],'Content-Type':'application/gzip'})
   with urllib.request.build_opener(NoRedirect).open(request,timeout=30) as response:ack=json.loads(response.read(4096))
   if ack.get('ok') is not True or ack.get('date')!=str(day) or ack.get('interval')!=interval:raise ValueError('Realtime acknowledgement mismatch')
   sent+=1
  if day!=today:
   state['cursor']=str(day-timedelta(days=1));write_state(path,state)
 state['cycle_day']=str(today);write_state(path,state)
 return {'realtime_sent':sent}
