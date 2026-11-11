"""Private local preview adapter."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.cache/mysql-client'))
sys.path.insert(0,str(ROOT/'uploader'))
from realtime_source import read_realtime as read_source
def read_realtime(day=None,interval=1):
 return read_source(day,interval,json.loads((ROOT/'.local/mysql-readonly.json').read_text(encoding='utf-8')))
