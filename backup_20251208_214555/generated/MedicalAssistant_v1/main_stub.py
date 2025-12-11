import http.server
import socketserver
import json
import threading
import os
from urllib.parse import urlparse

PORT = 8080
ROOT = os.path.dirname(__file__)
CHILD_JSON = os.path.join(ROOT, 'child_system.json')

with open(CHILD_JSON, 'r', encoding='utf-8') as f:
    child = json.load(f)

# Exec engine_management code to provide EngineManager
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
        p = urlparse(self.path)
        if p.path == '/':
            meta = child.get('metadata', {})
            return self._send_json({'name': meta.get('name'), 'parent': meta.get('parent')})
        elif p.path == '/capabilities':
            return self._send_json({'capabilities': child.get('capabilities', [])})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        p = urlparse(self.path)
        if p.path == '/process':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length else ''
            try:
                payload = json.loads(body) if body else {}
            except Exception:
                payload = {}
            # Determine routing: if payload contains 'engine' call process_with_engine, else route_task
            if payload.get('engine') and engine_manager:
                res = engine_manager.process_with_engine(payload.get('engine'), payload.get('data'))
                return self._send_json({'result': res})
            elif payload.get('task_type') and engine_manager:
                res = engine_manager.route_task(payload.get('task_type'), payload.get('task_data'))
                return self._send_json({'result': res})
            else:
                # fallback: echo
                return self._send_json({'result': 'no-op', 'payload': payload})
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Stub server serving at port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Stopping')
            httpd.server_close()
