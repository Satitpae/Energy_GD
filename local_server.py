"""Loopback-only TOU trial server, with a fresh file index on every request."""
import json
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
TOU_FOLDER = ROOT / 'TOU File for test'
TOU_NAME = re.compile(r'D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou', re.I)

def list_tou_files(folder):
    if not folder.is_dir():
        return []
    files = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file() and TOU_NAME.fullmatch(path.name):
            stat = path.stat()
            files.append({'name': path.name, 'size': stat.st_size})
    return files

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path != '/api/tou-files':
            return super().do_GET()
        try:
            payload = json.dumps({'files': list_tou_files(TOU_FOLDER)}).encode('utf-8')
        except OSError:
            self.send_error(500, 'Cannot read TOU folder')
            return
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

if __name__ == '__main__':
    with ThreadingHTTPServer(('127.0.0.1', 8766), Handler) as server:
        print('TOU Dashboard: http://127.0.0.1:8766/dashboard/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
