import http.server
import socketserver
import json
import os

PORT = 8000
ARTIFACTS_DIR = os.path.join(os.getcwd(), "artifacts")
DREAM_FILE = os.path.join(ARTIFACTS_DIR, "dream_knowledge.json")

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """
    Handles HTTP requests for the AGL System Dashboard.
    
    This handler serves:
    1. The main dashboard UI (HTML/CSS/JS) at root '/'.
    2. The JSON data API at '/api/data' for fetching system logs and dreams.
    """
    
    def do_GET(self):
        """
        Process GET requests.
        
        Routes:
            /api/data: Returns JSON data from 'dream_knowledge.json'.
            / or /index.html: Returns the dashboard HTML interface.
        """
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            data = []
            if os.path.exists(DREAM_FILE):
                try:
                    with open(DREAM_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    data = [{"error": str(e)}]
            
            # Sort by timestamp desc
            try:
                data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            except:
                pass
                
            self.wfile.write(json.dumps(data).encode())
            return

        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AGL System Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }
        h1 { color: #61dafb; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .card { background-color: #252526; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #ce9178; }
        .timestamp { color: #569cd6; font-size: 0.9em; margin-bottom: 5px; }
        .type-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 10px; }
        .type-consolidation { background-color: #4ec9b0; color: #1e1e1e; }
        .type-synthetic_dream { background-color: #c586c0; color: #1e1e1e; }
        .content { white-space: pre-wrap; line-height: 1.5; }
        #status { margin-bottom: 20px; padding: 10px; background-color: #3c3c3c; border-radius: 5px; }
        .refresh-btn { background-color: #0e639c; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background-color: #1177bb; }
    </style>
</head>
<body>
    <h1>🧠 AGL System Dashboard (لوحة التحكم)</h1>
    
    <div id="status">
        <strong>حالة النظام:</strong> <span style="color: #4ec9b0">نشط (Active)</span> | 
        <strong>المحرك:</strong> Advanced Proto-AGI |
        <strong>المنفذ:</strong> 8000
    </div>

    <!-- Quantum Controls Section -->
    <div class="card" style="border-left: 5px solid #c586c0;">
        <h3>⚛️ التحكم الكمومي (Quantum Controls)</h3>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <button onclick="checkQuantumStatus()" class="refresh-btn" style="background-color: #4ec9b0; color: #1e1e1e;">فحص الحالة (Status)</button>
            <button onclick="triggerVolition()" class="refresh-btn" style="background-color: #ce9178; color: #1e1e1e;">تفعيل الإرادة (Volition)</button>
            <button onclick="triggerInsight()" class="refresh-btn" style="background-color: #569cd6; color: #1e1e1e;">طلب استبصار (Insight)</button>
        </div>
        <div id="quantum-result" style="margin-top: 10px; padding: 10px; background-color: #1e1e1e; border-radius: 4px; font-family: monospace; white-space: pre-wrap; display: none; direction: ltr;"></div>
    </div>

    <div id="container">
        <p>جاري تحميل البيانات...</p>
    </div>

    <script>
        // Quantum Functions
        async function callQuantumEndpoint(url, method = 'GET', body = null) {
            const resultDiv = document.getElementById('quantum-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '⏳ جاري الاتصال بالنظام الكمومي...';
            
            try {
                const options = { method };
                if (body) {
                    options.headers = { 'Content-Type': 'application/json' };
                    options.body = JSON.stringify(body);
                }
                
                const response = await fetch(url, options);
                const data = await response.json();
                resultDiv.innerHTML = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.innerHTML = '❌ خطأ: ' + error.message;
            }
        }

        function checkQuantumStatus() {
            callQuantumEndpoint('/quantum/status');
        }

        function triggerVolition() {
            callQuantumEndpoint('/quantum/volition', 'POST');
        }

        function triggerInsight() {
            const inputs = prompt("أدخل نصاً للتحليل (أو اترك فارغاً لاستخدام الافتراضي):");
            const payload = {
                inputs: inputs ? [inputs] : [
                    "Quantum coherence in biological systems",
                    "The hard problem of consciousness",
                    "Neural synchronization frequencies"
                ]
            };
            callQuantumEndpoint('/quantum/insight', 'POST', payload);
        }

        // Existing Data Fetcher
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                const container = document.getElementById('container');
                
                if (data.length === 0) {
                    container.innerHTML = '<p>لا توجد بيانات متاحة حالياً في سجل الأحلام.</p>';
                    return;
                }

                let html = '';
                data.forEach(item => {
                    let typeClass = 'type-' + item.type;
                    let typeName = item.type === 'consolidation' ? 'دمج ذكريات' : 'حلم اصطناعي';
                    if (item.type === 'synthetic_dream') typeName = 'حلم إبداعي';
                    
                    html += `
                        <div class="card">
                            <div class="timestamp">
                                ${item.timestamp}
                                <span class="type-badge ${typeClass}">${typeName}</span>
                                ${item.topic ? `<span class="type-badge" style="background-color: #dcdcaa; color: #1e1e1e">${item.topic}</span>` : ''}
                            </div>
                            <div class="content">${item.content}</div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } catch (error) {
                document.getElementById('container').innerHTML = '<p style="color: #f48771">خطأ في تحميل البيانات. تأكد من تشغيل الخادم.</p>';
                console.error('Error:', error);
            }
        }

        fetchData();
        setInterval(fetchData, 5000); // Refresh every 5 seconds
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode('utf-8'))
            return
            
        # Fallback
        self.send_error(404)

print(f"Serving dashboard at http://localhost:{PORT}")
with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
    httpd.serve_forever()
