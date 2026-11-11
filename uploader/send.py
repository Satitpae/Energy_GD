"""TOU folder uploader. Python standard library only; no third-party packages."""
import argparse
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import time
import sys
import threading
from http.client import HTTPException
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_BYTES = 128 * 1024
NAME = re.compile(r'D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou', re.I)

class UploadRejected(OSError):
    """The server rejected these contents; retry only after a change or explicit reset."""

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OSError('Upload redirected; check base_url')

def send_http(config, name, body):
    base = config['base_url'].rstrip('/')
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError('base_url must be an HTTPS origin, without path or credentials')
    token = os.environ.get('EMS_UPLOAD_TOKEN') or config.get('upload_token', '')
    if not token or token.startswith('REPLACE_'):
        raise ValueError('Set upload_token or EMS_UPLOAD_TOKEN')
    params = {'site': config.get('site', 'main'), 'name': name}
    route = '/api/upload'
    if config.get('api_style') == 'php':
        route = '/api/index.php'
        params['action'] = 'upload'
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(base + route + '?' + query, data=body, method='POST', headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/octet-stream'})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            ack = json.load(response)
            if not isinstance(ack, dict) or ack.get('ok') is not True or ack.get('size') != len(body):
                raise OSError('Server did not confirm complete upload')
    except urllib.error.HTTPError as error:
        if error.code in (400, 413, 422):
            raise UploadRejected('Upload HTTP ' + str(error.code)) from None
        raise OSError('Upload HTTP ' + str(error.code)) from None

def send_heartbeat(config, scan_ok):
    base=config['base_url'].rstrip('/')
    parsed=urllib.parse.urlsplit(base)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
        raise ValueError('Invalid heartbeat destination')
    token=os.environ.get('EMS_UPLOAD_TOKEN') or config.get('upload_token','')
    if not token:raise ValueError('Missing upload token')
    params=urllib.parse.urlencode({'action':'sender-heartbeat','site':config.get('site','main')})
    body=json.dumps({'scan_ok':scan_ok}).encode('utf-8')
    request=urllib.request.Request(base+'/api/index.php?'+params,data=body,method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=15) as response:
            ack=json.load(response)
            if not isinstance(ack,dict) or ack.get('ok') is not True:raise OSError('Heartbeat not acknowledged')
            return ack
    except urllib.error.HTTPError as error:raise OSError('Heartbeat HTTP '+str(error.code)) from None

def write_state(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2), encoding='utf-8')
    os.replace(temp, path)

def scan_once(config, sender=send_http, dry_run=False, today=None, stop_requested=None):
    folder = Path(config['folder']).resolve()
    if not folder.is_dir():
        raise ValueError('TOU folder does not exist')
    state_path = Path(config['state_file'])
    source = '|'.join([config['base_url'].rstrip('/'), config.get('site', 'main'), str(folder)])
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    if state.get('source') != source:
        state = {'source': source, 'files': {}}
    state.setdefault('rejected', {})
    state.setdefault('daily', {})
    today = today or time.strftime('%Y-%m-%d')
    scheduled = config.get('upload_policy') == 'latest-month-daily-history'
    paths = sorted(p for p in folder.iterdir() if p.is_file() and NAME.fullmatch(p.name))
    months = {m.lower(): i+1 for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}
    def period(path):
        return (2000+int(path.stem[-2:]), months[path.stem[3:6].lower()])
    latest = {}
    for path in paths:
        meter = path.name[:3].upper()
        latest[meter] = max(latest.get(meter, (0,0)), period(path))
    result = {'sent': 0, 'unchanged': 0, 'failed': 0, 'pending': 0, 'rejected': 0, 'history_wait': 0, 'errors': []}
    for path in paths:
        if stop_requested and stop_requested():
            result['stopped'] = True
            break
        historical = scheduled and period(path) < latest[path.name[:3].upper()]
        if historical and state['daily'].get(path.name) == today and not (config.get('retry_rejected') and path.name in state['rejected']):
            result['history_wait'] += 1
            continue
        try:
            before = path.stat()
            if before.st_size > MAX_BYTES:
                raise ValueError('File exceeds 128 KiB')
            with path.open('rb') as stream:
                body = stream.read(MAX_BYTES + 1)
            after = path.stat()
            if len(body) > MAX_BYTES or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError('File changed while reading; retry next scan')
            fingerprint = hashlib.sha256(body).hexdigest()
            if not historical and state['files'].get(path.name) == fingerprint:
                result['unchanged'] += 1
                continue
            if not historical and not config.get('retry_rejected') and state['rejected'].get(path.name, {}).get('hash') == fingerprint:
                result['rejected'] += 1
                continue
            if dry_run:
                result['pending'] += 1
                continue
            try:
                sender(config, path.name, body)
            except UploadRejected as error:
                state['rejected'][path.name] = {'hash': fingerprint, 'error': str(error)}
                if historical: state['daily'][path.name] = today
                write_state(state_path, state)
                raise
            state['files'][path.name] = fingerprint
            state['rejected'].pop(path.name, None)
            if historical: state['daily'][path.name] = today
            write_state(state_path, state)
            result['sent'] += 1
        except (OSError, ValueError, HTTPException) as error:
            result['failed'] += 1
            result['errors'].append(path.name + ': ' + str(error))
    return result

def main():
    parser = argparse.ArgumentParser(description='Upload new or changed TOU files every 60 seconds')
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('config.local.json'))
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--retry-rejected', action='store_true')
    parser.add_argument('--stop', action='store_true')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    for key in ['folder', 'state_file']:
        config[key] = str((config_path.parent / config[key]).resolve())
    config['retry_rejected'] = args.retry_rejected
    state_path = Path(config['state_file'])
    stop_path = state_path.with_name('sender.stop')
    lock_path = state_path.with_name('sender.lock')
    if args.stop:
        stop_path.touch()
        print('Stop requested. The sender will finish its current scan and stop.')
        return 0
    lock = None
    if args.status or not args.dry_run:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = lock_path.open('a+b')
        if lock_path.stat().st_size == 0:
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lock.close()
            if sys.stdout: print('RUNNING' if args.status else 'Sender already running; no second instance started.')
            return 0
        if args.status:
            lock.close()
            print('STOPPED')
            return 0
        stop_path.unlink(missing_ok=True)
    logger = logging.getLogger('tou-sender')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    if sys.stdout: logger.addHandler(logging.StreamHandler(sys.stdout))
    log_path = config_path.parent / config.get('log_file', 'logs/tou-sender.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.addHandler(RotatingFileHandler(log_path, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8'))
    for handler in logger.handlers: handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    interval = max(10, int(config.get('interval_seconds', 60)))
    heartbeat_enabled=config.get('api_style')=='php' and config.get('heartbeat_enabled',True) and not args.dry_run
    heartbeat_stop=threading.Event();heartbeat_thread=None;scan_health=None
    def contact_sender():
        try:
            ack=send_heartbeat(config,scan_health)
            logger.info('Sender contact acknowledged at %s',ack.get('last_seen_at',''))
        except (OSError,ValueError,HTTPException) as error:logger.warning('Sender contact failed: %s',str(error))
    def heartbeat_loop():
        while not heartbeat_stop.is_set():
            contact_sender()
            heartbeat_stop.wait(60)
    if heartbeat_enabled and not args.once:
        heartbeat_thread=threading.Thread(target=heartbeat_loop,daemon=True);heartbeat_thread.start()
    try:
        while True:
            if not args.once and not args.dry_run and stop_path.exists():
                logger.info('Sender stopped by request.')
                return 0
            try:
                result = scan_once(config, dry_run=args.dry_run, stop_requested=lambda: stop_path.exists())
                scan_health=result['failed']==0
                logger.info(json.dumps(result, ensure_ascii=False))
                if config.get('realtime',{}).get('enabled') and not args.dry_run:
                    try:
                        from realtime_sync import sync_once
                        logger.info(json.dumps(sync_once(config,config_path.parent/'realtime-state.json',lambda:stop_path.exists())))
                    except Exception:logger.error('Realtime synchronization failed; retry next scan')
            except (OSError, ValueError, HTTPException) as error:
                scan_health=False
                logger.error('Scan failed: ' + str(error))
                if args.once:
                    if heartbeat_enabled:contact_sender()
                    return 1
            else:
                if args.once or args.dry_run:
                    if heartbeat_enabled:contact_sender()
                    return 1 if result['failed'] else 0
            for _ in range(interval):
                if stop_path.exists(): break
                time.sleep(1)
    except KeyboardInterrupt:
        return 0
    finally:
        heartbeat_stop.set()
        if heartbeat_thread:heartbeat_thread.join(timeout=2)
        if lock: lock.close()

if __name__ == '__main__':
    raise SystemExit(main())
