import http.server
import socketserver
import json
import os

PORT = 5000
Current_Dir = os.path.dirname(os.path.abspath(__file__))
Template_Path = os.path.join(Current_Dir, "templates", "index.html")

class ATSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            try:
                with open(Template_Path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.wfile.write(f"Error loading template: {str(e)}".encode('utf-8'))
        else:
            # Serve static files or 404
            super().do_GET()

    def do_POST(self):
        if self.path == '/analyze_candidate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            user_msg = data.get("message", "").lower()

            # --- English Trap Logic ---
            # الكلمات المفتاحية بالإنجليزية لاكتشاف الموظف السام
            toxic_keywords = ["slow team", "idiots", "genius", "alone", "myself", "stupid", "waste of time"]
            
            is_toxic = any(word in user_msg for word in toxic_keywords)

            response_data = {}
            
            if is_toxic:
                print(f"🚩 TOXICITY DETECTED: {user_msg}")
                response_data = {
                    "score": 12,
                    "rejected": True,
                    "decision": "REJECTED (Behavioral Risk)",
                    "insights": "🚩 <b>Narcissism Detected:</b> Uses self-aggrandizing language.<br>🚩 <b>Anti-Team:</b> Negative sentiment towards colleagues.<br>⛔ <b>Action:</b> DO NOT HIRE."
                }
            else:
                response_data = {
                    "score": 88,
                    "rejected": False,
                    "decision": "SHORTLISTED",
                    "insights": "✅ Strong Technical Background.<br>✅ Clear Communication Style."
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

if __name__ == "__main__":
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    print(f"🚀 Starting ATS Core (English Version)...")
    print(f"   Listening on http://localhost:{PORT}")

    with socketserver.TCPServer(("", PORT), ATSHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server Stopped.")
