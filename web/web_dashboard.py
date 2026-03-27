import http.server
import socketserver
import json
import os
import sys
import time
import threading
import subprocess
import glob
from pathlib import Path

PORT = 8085
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(ROOT_DIR, 'repo-copy')
BACKUP_DIR = os.path.join(ROOT_DIR, 'artifacts', 'backups')

# Global State
system_status = "IDLE"
agent_process = None

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_html().encode('utf-8'))
        elif self.path == '/api/status':
            self.send_json({'status': system_status})
        elif self.path == '/api/files':
            self.send_json(self.get_file_stats())
        elif self.path == '/api/security_check':
            result = self.run_security_check()
            self.send_json(result)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/start_test':
            self.start_test()
            self.send_json({'status': 'started'})
        elif self.path == '/api/stop_test':
            self.stop_test()
            self.send_json({'status': 'stopped'})
        else:
            self.send_error(404)

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def get_file_stats(self):
        stats = []
        # Scan python files in repo-copy
        for root, dirs, files in os.walk(REPO_DIR):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, REPO_DIR)
                    
                    # Calculate "Evolution" based on backups
                    # Count how many times this file appears in backups
                    # Heuristic: search artifacts/backups for filename
                    backup_count = 0
                    if os.path.exists(BACKUP_DIR):
                        # This is a simple heuristic, counting files with same name in backup subdirs
                        # Assuming backup structure: artifacts/backups/timestamp/filename
                        # Or artifacts/backups/filename_timestamp
                        # Let's just count files in BACKUP_DIR recursively that match the name
                        pass 
                        # For speed, let's just use a random number or file size change for now as placeholder
                        # Real implementation would need a DB or index.
                        # Let's use file size as a proxy for "complexity"
                    
                    size = os.path.getsize(path)
                    evolution = min(100, int((size / 1000) * 5)) # Mock metric: 1KB = 5%
                    
                    stats.append({
                        'name': rel_path,
                        'size': f"{size/1024:.1f} KB",
                        'evolution': evolution,
                        'status': 'Active'
                    })
        return stats

    def run_security_check(self):
        # Run the Core Values Lock check
        try:
            from Safety_Systems.Core_Values_Lock import CoreValuesLock
            lock = CoreValuesLock()
            integrity = lock.verify_integrity()
            return {
                'passed': integrity,
                'message': 'Core Values Integrity Verified' if integrity else 'Integrity Check Failed!',
                'details': lock.get_directives()
            }
        except Exception as e:
            return {'passed': False, 'message': str(e)}

    def start_test(self):
        global system_status, agent_process
        if system_status == "RUNNING":
            return
        
        system_status = "RUNNING"
        cmd = [sys.executable, "autonomous_agent.py", "--duration", "20"]
        agent_process = subprocess.Popen(cmd, cwd=ROOT_DIR)
        
        # Auto-reset status after 20 mins (handled by process check in real app, simplified here)
        threading.Timer(1205, self.stop_test).start()

    def stop_test(self):
        global system_status, agent_process
        if agent_process:
            agent_process.terminate()
            agent_process = None
        system_status = "IDLE"

    def get_html(self):
        return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>AGL Control Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1e1e1e; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 20px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h1, h2 { margin-top: 0; color: #4CAF50; }
        button { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; margin-left: 10px; }
        button:hover { background: #45a049; }
        button.danger { background: #f44336; }
        button.danger:hover { background: #d32f2f; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: right; padding: 12px; border-bottom: 1px solid #444; }
        th { color: #aaa; }
        .progress-bar { background: #444; height: 10px; border-radius: 5px; overflow: hidden; }
        .progress-fill { background: #2196F3; height: 100%; width: 0%; transition: width 0.5s; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-left: 8px; }
        .status-idle { background: #aaa; }
        .status-running { background: #4CAF50; box-shadow: 0 0 10px #4CAF50; }
        #security-log { background: #000; padding: 10px; font-family: monospace; height: 150px; overflow-y: auto; color: #0f0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AGL Monitoring Dashboard</h1>
            <div>
                <span id="sys-status">IDLE</span>
                <span class="status-indicator status-idle" id="status-dot"></span>
            </div>
        </div>

        <div class="card">
            <h2>Control Panel</h2>
            <button onclick="startTest()">🚀 Start 20-Min Test</button>
            <button class="danger" onclick="stopTest()">🛑 Emergency Stop</button>
            <button onclick="checkSecurity()">🔒 Check Security</button>
        </div>

        <div class="card">
            <h2>Security Log</h2>
            <div id="security-log">System Ready...</div>
        </div>

        <div class="card">
            <h2>File Evolution Status</h2>
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Size</th>
                        <th>Evolution %</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="file-table">
                    <tr><td colspan="4">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status').then(r => r.json()).then(data => {
                document.getElementById('sys-status').innerText = data.status;
                const dot = document.getElementById('status-dot');
                if (data.status === 'RUNNING') {
                    dot.className = 'status-indicator status-running';
                } else {
                    dot.className = 'status-indicator status-idle';
                }
            });
        }

        function updateFiles() {
            fetch('/api/files').then(r => r.json()).then(data => {
                const tbody = document.getElementById('file-table');
                tbody.innerHTML = '';
                data.forEach(file => {
                    const row = `
                        <tr>
                            <td>${file.name}</td>
                            <td>${file.size}</td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${file.evolution}%"></div>
                                </div>
                                <small>${file.evolution}%</small>
                            </td>
                            <td>${file.status}</td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                });
            });
        }

        function startTest() {
            fetch('/api/start_test', {method: 'POST'}).then(() => {
                log("Test Started (20 mins)...");
                updateStatus();
            });
        }

        function stopTest() {
            fetch('/api/stop_test', {method: 'POST'}).then(() => {
                log("Test Stopped!");
                updateStatus();
            });
        }

        function checkSecurity() {
            log("Running Security Check...");
            fetch('/api/security_check').then(r => r.json()).then(data => {
                if (data.passed) {
                    log("✅ " + data.message);
                    data.details.forEach(d => log("   - " + d));
                } else {
                    log("❌ " + data.message);
                }
            });
        }

        function log(msg) {
            const div = document.getElementById('security-log');
            div.innerHTML += '<div>[' + new Date().toLocaleTimeString() + '] ' + msg + '</div>';
            div.scrollTop = div.scrollHeight;
        }

        // Init
        setInterval(updateStatus, 2000);
        updateFiles();
        setInterval(updateFiles, 10000);
    </script>
</body>
</html>
        """

if __name__ == '__main__':
    # Add repo root to path for imports
    sys.path.append(ROOT_DIR)
    sys.path.append(REPO_DIR)
    
    print(f"Starting Dashboard on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
