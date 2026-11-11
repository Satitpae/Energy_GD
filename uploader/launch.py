"""Start/stop only this TOU sender, without a visible background console."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['start','stop','status','once','retry'])
    parser.add_argument('--config',type=Path,default=Path(__file__).with_name('config.local.json'))
    args=parser.parse_args()
    command=[sys.executable,str(Path(__file__).with_name('send.py')), '--config',str(args.config.resolve())]
    if args.action=='start':
        status=subprocess.run(command+['--status'],capture_output=True,text=True,check=True).stdout.strip()
        if status=='RUNNING':
            print('TOU sender is already running.');return 0
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        subprocess.Popen(command,creationflags=flags,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=os.name!='nt')
        time.sleep(1)
        status=subprocess.run(command+['--status'],capture_output=True,text=True,check=True).stdout.strip()
        print('TOU sender: '+status+' | log: '+str(args.config.resolve().parent/'logs/tou-sender.log'))
        return 0 if status=='RUNNING' else 1
    return subprocess.call(command+({'stop':['--stop'],'status':['--status'],'once':['--once'],'retry':['--once','--retry-rejected']}[args.action]))

if __name__=='__main__':raise SystemExit(main())
