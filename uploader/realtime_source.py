"""Read-only MySQL adapter for localhost preview only; no storage of readings."""
import sys,json
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pymysql
FIELDS=['kW','kWh','Demand','AccDem','kVA','kVar','PF','Hz','VoltageL1','VoltageL2','VoltageL3','CurrentL1','CurrentL2','CurrentL3','THDVoltageL1','THDVoltageL2','THDVoltageL3','THDCurrentL1','THDCurrentL2','THDCurrentL3']
def read_realtime(day=None,interval=1,config=None):
 interval=int(interval)
 mapping={5:0,15:1,30:2,60:3}
 if interval not in [1,5,15,30,60]:raise ValueError("Unsupported interval")
 cfg=config
 c=pymysql.connect(**cfg,connect_timeout=4,read_timeout=8,write_timeout=4,autocommit=False,cursorclass=pymysql.cursors.DictCursor)
 now=datetime.now(timezone(timedelta(hours=7)));devices=[]
 start=datetime.strptime(day,'%Y-%m-%d') if day else (now-timedelta(hours=24)).replace(tzinfo=None)
 end=start+timedelta(days=1) if day else now.replace(tzinfo=None)
 bounds=' AND DataDateTime >= %s AND DataDateTime < %s' if day else ''
 def params(name):return (name,start,end) if day else (name,)
 try:
  with c.cursor() as q:
   q.execute('SET TRANSACTION READ ONLY');q.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
   for name in ['MEA','Solar Cell']:
    q.execute('SELECT DataDateTime FROM datatbl_energy WHERE Device=%s'+bounds+' ORDER BY DataDateTime DESC LIMIT 1',params(name));row=q.fetchone();last_row=row['DataDateTime'] if row else None
    q.execute('SELECT DataDateTime,'+','.join('`'+f+'`' for f in FIELDS)+' FROM datatbl_energy WHERE Device=%s AND kW IS NOT NULL'+bounds+' ORDER BY DataDateTime DESC LIMIT 1',params(name));latest=q.fetchone()
    q.execute('SELECT DataDateTime,kW FROM datatbl_energy WHERE Device=%s AND DataDateTime >= %s AND DataDateTime < %s AND kW IS NOT NULL ORDER BY kW DESC,DataDateTime ASC LIMIT 1',(name,start,end));peak=q.fetchone()
    if interval==1:
     q.execute('SELECT DataDateTime,'+','.join('`'+f+'`' for f in FIELDS)+' FROM datatbl_energy WHERE Device=%s AND DataDateTime >= %s AND DataDateTime < %s ORDER BY DataDateTime DESC LIMIT 1440',(name,start,end))
    else:
     q.execute('SELECT DataDateTime,'+','.join('`'+f+'`' for f in FIELDS)+' FROM datatbl_energy_summary WHERE Device=%s AND AggregateType=%s AND ShiftID=0 AND DataDateTime >= %s AND DataDateTime < %s ORDER BY DataDateTime ASC LIMIT 1440',(name,mapping[interval],start,end))
    history=list(q.fetchall())
    if interval==1:history.reverse()
    age=(now-latest['DataDateTime'].replace(tzinfo=now.tzinfo)).total_seconds() if latest else None
    devices.append({'name':name,'last_row_at':last_row,'latest':latest,'age_seconds':age,'stale':age is None or age>180,'history':history,'daily_peak':peak})
  return {'ok':True,'server_time':now.isoformat(),'selected_date':day,'window_end':end.replace(tzinfo=now.tzinfo).isoformat(),'interval_minutes':interval,'devices':devices}
 finally:c.rollback();c.close()
