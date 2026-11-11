"""Desktop settings and command routing; no GUI or network during import."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

def validate_config(config,require_token=True):
    url=urlsplit(config.get('base_url',''))
    if url.scheme!='https' or not url.netloc or url.username or url.password or url.query or url.fragment or url.path not in ('','/'):
        raise ValueError('ต้องใช้ปลายทาง HTTPS ที่ถูกต้อง')
    if require_token and not config.get('upload_token'):raise ValueError('กรุณาเลือกไฟล์ตั้งค่าการเชื่อมต่อก่อนเริ่มส่ง')

def ensure_config(data_dir,seed):
    path=Path(data_dir)/'config.json'
    defaults={'state_file':'state.json','log_file':'logs/tou-sender.log','interval_seconds':60,'api_style':'php','upload_policy':'latest-month-daily-history'}
    if path.exists():
        existing=json.loads(path.read_text(encoding='utf-8-sig'))
        config={**defaults,**existing}
        validate_config(config,require_token=False)
        if config!=existing:save_config(path,config,require_token=False)
        return path
    config={**seed,**defaults}
    validate_config(config,require_token=False)
    path.parent.mkdir(parents=True,exist_ok=True)
    save_config(path,config,require_token=False)
    return path

def save_config(path,config,require_token=True):
    validate_config(config,require_token=require_token)
    path=Path(path);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
    os.replace(temp,path)

def command_for(action,config_path,frozen=None,executable=None):
    frozen=getattr(sys,'frozen',False) if frozen is None else frozen
    executable=executable or sys.executable
    args=[executable]
    if not frozen:args.append(str(Path(__file__).with_name('desktop_app.py')))
    args+=['--engine','--config',str(config_path)]
    args+={'start':[],'status':['--status'],'stop':['--stop'],'once':['--once']}[action]
    return args

def acquire_lock(data_dir,name):
    path=Path(data_dir)/name;path.parent.mkdir(parents=True,exist_ok=True)
    lock=path.open('a+b')
    if path.stat().st_size==0:lock.write(b'0');lock.flush()
    lock.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:lock.close();return None
    return lock

def is_running(data_dir,name='sender.lock'):
    path=Path(data_dir)/name
    if not path.exists():return False
    with path.open('r+b') as lock:
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:return True
    return False

def default_data_dir():
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'GrandDigital'/'TOUSender'
