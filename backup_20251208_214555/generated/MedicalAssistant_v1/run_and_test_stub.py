import http.server
import socketserver
import json
import threading
import os
import time
from urllib.request import urlopen

PORT = 8080
ROOT = os.path.dirname(__file__)
CHILD_JSON = os.path.join(ROOT, 'child_system.json')

with open(CHILD_JSON, 'r', encoding='utf-8') as f:
    child = json.load(f)

ns = {}
exec(child['components']['engine_management'], ns)
EngineManager = ns.get('EngineManager')
engine_manager = EngineManager() if EngineManager else None

class Handler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            meta = child.get('metadata', {})
            return self._send_json({'name': meta.get('name'), 'parent': meta.get('parent')})
        elif self.path == '/capabilities':
            return self._send_json({'capabilities': child.get('capabilities', [])})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/process':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length else ''
            try:
                payload = json.loads(body) if body else {}
            except Exception:
                payload = {}
            if payload.get('engine') and engine_manager:
                res = engine_manager.process_with_engine(payload.get('engine'), payload.get('data'))
                return self._send_json({'result': res})
            elif payload.get('task_type') and engine_manager:
                res = engine_manager.route_task(payload.get('task_type'), payload.get('task_data'))
                return self._send_json({'result': res})
            else:
                return self._send_json({'result': 'no-op', 'payload': payload})
        else:
            self.send_response(404)
            self.end_headers()

# start server in background thread
httpd = socketserver.TCPServer(('', PORT), Handler)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()
print('server started')

# give server a moment
time.sleep(0.5)

# test root
try:
    r = urlopen(f'http://127.0.0.1:{PORT}/', timeout=2)
    print('root status', r.status)
    print('root body', r.read().decode())
except Exception as e:
    print('root err', e)

# test process route (engine call)
import urllib.request
req = urllib.request.Request(f'http://127.0.0.1:{PORT}/process', data=json.dumps({'engine':'MathematicalBrain','data':{'symptoms':'fever'}}).encode('utf-8'), headers={'Content-Type':'application/json'})
try:
    r = urllib.request.urlopen(req, timeout=2)
    print('process status', r.status)
    print('process body', r.read().decode())
except Exception as e:
    print('process err', e)

# shutdown
httpd.shutdown()
httpd.server_close()
print('server stopped')
