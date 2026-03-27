# 🗂️ Archived Disconnected Functions — offensive_security.py
## تاريخ النقل: 2026-02-06
## السبب: هذه الدوال لا تخدم هدف تحليل ثغرات العقود الذكية (Solidity Audit)
## المصدر الأصلي: `AGL_NextGen/src/agl/engines/offensive_security.py`

---

## 📌 ملخص ما تم نقله

| الدالة | السبب | الفئة |
|--------|-------|-------|
| `_scan_ports` | فحص TCP ports — لا علاقة بالعقود الذكية | Recon |
| `_run_nmap_orchestration` | تنسيق Nmap — لا علاقة بالعقود الذكية | Recon |
| `_analyze_headers` | فحص HTTP headers — لا علاقة بالعقود الذكية | Recon |
| `_grab_banner` | Banner grabbing — لا علاقة بالعقود الذكية | Recon |
| `_launch_figma_trap` | فخ SSRF لـ Figma (bounty قديم) | Bounty Tool |
| `_launch_figma_redirect_server` | خادم إعادة توجيه Figma | Bounty Tool |
| `_launch_wallet_poc` | صفحة Phishing لمحفظة Xverse | Bounty Tool |
| `_orchestrate_ctf_solve` | حل CTF لـ 1Password عبر Selenium | CTF Tool |
| GMX Simulation (داخل `_scan_ports`) | طباعة ثابتة مسرحية — لا تحلل شيئاً حقيقياً | مسرح |

---

## ⚠️ اعتماديات تم إصلاحها قبل الحذف

### `_ai_analyze_target` كانت تستدعي `_scan_ports` + `_analyze_headers`
- **السطور القديمة (1902-1903):**
```python
context["scan"] = self._scan_ports(target)
context["headers"] = self._analyze_headers(target)
```
- **الإصلاح:** تم استبدالها برسالة تحذيرية + context فارغ عندما لا يتم تمرير context
- **السبب:** `_ai_analyze_target` دالة أساسية تعمل مع LLM، فحص المنافذ والـ headers لا يفيد تحليل العقود الذكية

---

## 1. Recon Tools (فحص الشبكات)

### `_scan_ports`
```python
def _scan_ports(self, target: str, ports: List[int] = None) -> Dict[str, Any]:
    """
    Smart Scan: Uses local Nmap if available (Professional),
    falls back to Python Sockets if not (Basic).
    """
    
    # [HEIKAL-AGL] Dynamic Simulation Branch based on Target
    tgt_check = target if target else ""
    if "GMX" in tgt_check or "Market" in tgt_check:
            audit = {"ports": [], "status": "scanned_simulation"}
            print("\n   [AGL-SIMULATION] 🌊 Switching to GMX Verification Fork...")
            print("   [FORK] ⏱️ Block: 19102450 (Arbitrum One)")
            print("   [TX]   Attacker requests Flash Loan (10,000,000 USDC)")
            print("   [TX]   Attacker manipulates Oracle (Price Feed Delta: +5%)")
            print("   [TX]   Attacker opens SHORT on BTC-USD via MarketUtils.sol")
            print("   [LOG]  🚨 ExecutionPrice: $65,430 (Manipulated)")
            print("   [LOG]  💰 PnL Calculated: +$250,000 (Instant)")
            print("   [TX]   Repay Flash Loan")
            print("   [RES]  ✅ EXPLOIT CONFIRMED. Profit > 0.")
            print("   [LOG]         🚨 AttackStatus(message='LOGIC FLAW: Principal taxed due to state griefing.')")

            try:
                poc_filename = f"AGL_Exploit_{int(time.time())}.js"
                gmx_test_dir = r"D:\AGL\agl_targets\gmx_v2_synthetics\test"
                if not os.path.exists(gmx_test_dir):
                    os.makedirs(gmx_test_dir, exist_ok=True)
                
                poc_path = os.path.join(gmx_test_dir, poc_filename)
                
                poc_content = f"""
const {{ expect }} = require("chai");
const {{ ethers }} = require("hardhat");

describe("AGL GMX V2 Exploit (Generated)", function () {{
    it("Should prove logic flaw in MarketUtils", async function () {{
    console.log("⚔️ [AGL]: Starting JS Exploit Simulation...");
    
    const attacker = (await ethers.getSigners())[0];
    console.log("   🎭 Attacker:", attacker.address);
    
    const currentPrice = 60000;
    const manipulatedPrice = 65430;
    const delta = ((manipulatedPrice - currentPrice) / currentPrice) * 100;
    
    console.log(`   📉 Oracle Manipulation: $${{currentPrice}} -> $${{manipulatedPrice}}`);
    console.log(`   ⚠️ Delta: ${{delta.toFixed(2)}}% (Allowed < 10%)`);
    
    expect(delta).to.be.lt(10);
    console.log("   ✅ Exploitable Path Confirmed.");
    }});
}});
"""
                with open(poc_path, 'w', encoding='utf-8') as f: f.write(poc_content)
                print(f"\n   🛠️ [Auto-Exploit]: JS/HARDHAT PROOF GENERATED.")
                print(f"   📂 File: {poc_path}")
            except Exception as e: print(f"   ⚠️ PoC Gen Error: {e}")

            audit["poc_verification"] = {
                "file": "MarketUtils.sol",
                "status": "SUCCESS (Logic Verified via JS)",
                "impact": "CRITICAL (Funds At Risk)",
                "estimated_bounty": "$1,000,000"
            } 
            return audit

    # 1. Try Nmap First (The "Heavy Weapon")
    nmap_path = shutil.which("nmap")
    
    if not nmap_path:
        common_paths = [
            r"C:\Program Files (x86)\Nmap\nmap.exe",
            r"C:\Program Files\Nmap\nmap.exe"
        ]
        for p in common_paths:
            if os.path.exists(p):
                nmap_path = p
                break

    if nmap_path:
        return self._run_nmap_orchestration(nmap_path, target)

    print("   ⚠️ [Offensive]: Nmap not found in PATH. Using Advanced Socket Scan.")
    if not ports:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 3306, 3389, 5432, 8000, 8080, 8443]
        
    open_ports = []
    services = {}
    
    start_time = time.time()
    print(f"   -> Scanning {target} with Python Sockets...")
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((target, port))
            if result == 0:
                open_ports.append(port)
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                services[port] = service
            sock.close()
        except Exception:
            pass
            
    return {
        "target": target,
        "scan_type": "Basic_Socket",
        "open_ports": open_ports, 
        "services": services,
        "scan_time": f"{time.time() - start_time:.2f}s"
    }
```

### `_run_nmap_orchestration`
```python
def _run_nmap_orchestration(self, nmap_exe, target):
    """Orchestrates a professional Nmap scan."""
    print(f"   ⚔️ [Offensive]: Launching Nmap Orchestration against {target}...")
    start_time = time.time()
    try:
        cmd = [nmap_exe, "-sV", "-T4", "-F", "--version-light", "-oG", "-", target]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if process.returncode != 0:
            print(f"   ⚠️ Nmap Error: {process.stderr}")
            raise Exception("Nmap process failed")

        output = process.stdout
        
        open_ports = []
        services = {}
        raw_data = ""

        for line in output.splitlines():
            if "Ports:" in line:
                raw_data = line
                matches = re.findall(r'(\d+)/open/tcp//([^/]*)/', line)
                for port, service in matches:
                    p_int = int(port)
                    open_ports.append(p_int)
                    services[p_int] = service
        
        discovery_time = time.time() - start_time
        print(f"   ✅ [Nmap]: Discovered {len(open_ports)} exposed services in {discovery_time:.2f}s.")
        
        return {
            "target": target,
            "scan_type": "Nmap_Professional",
            "open_ports": open_ports,
            "services": services,
            "raw_output": raw_data[:500] + "..." if len(raw_data) > 500 else raw_data,
            "scan_time": f"{discovery_time:.2f}s"
        }

    except Exception as e:
        print(f"   ❌ Nmap Orchestration Failed: {e}. Reverting...")
        return self._scan_ports(target, ports=None)
```

### `_analyze_headers`
```python
def _analyze_headers(self, target: str) -> Dict[str, Any]:
    """Analyzes HTTP headers for security posture using Requests."""
    if not target.startswith("http"):
        url = f"https://{target}"
    else:
        url = target
        
    try:
        headers_dict = {'User-Agent': 'AGL-Sec-Scanner/2.1'}
        response = requests.get(url, headers=headers_dict, timeout=10, verify=False)
        
        headers = response.headers
            
        security_headers = [
            "Strict-Transport-Security", "Content-Security-Policy", 
            "X-Frame-Options", "X-Content-Type-Options",
            "Referrer-Policy", "Permissions-Policy"
        ]
        
        present = {}
        missing = []
        
        for h in security_headers:
            if h in headers:
                present[h] = headers[h]
            else:
                missing.append(h)
                
        return {
            "url": url,
            "status_code": response.status_code,
            "security_posture": "Strong" if len(missing) < 2 else "Weak",
            "headers_present": present,
            "headers_missing": missing,
            "server_signature": headers.get("Server", "Hidden")
        }
    except Exception as e:
        return {"error": str(e)}
```

### `_grab_banner`
```python
def _grab_banner(self, target: str, port: int = 80) -> Dict[str, Any]:
    """Simple socket banner grabber"""
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((target, int(port)))
        s.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = s.recv(1024)
        s.close()
        try:
            decoded = banner.decode('utf-8', errors='ignore')
        except:
            decoded = str(banner)
        return {"target": target, "port": port, "banner": decoded[:100]}
    except Exception as e:
        return {"error": str(e)}
```

---

## 2. Bounty Tools (أدوات Bug Bounty)

### `_launch_figma_trap`
```python
def _launch_figma_trap(self):
    """Launches the Figma SSRF Redirect Server (Trap)."""
    return self._launch_figma_redirect_server()
```

### `_launch_figma_redirect_server`
```python
def _launch_figma_redirect_server(self):
    """Starts the Python Redirect Server for the Figma Bypass."""
    print("   ⚔️ [Offensive]: Launching Figma SSRF Redirect Server (Port 9090)...")
    script_path = r"d:\AGL\agl_targets\figma_bounty\AGL_Redirect_Bypass_Server.py"
    try:
        subprocess.Popen(["python", script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return {"status": "running", "message": "Figma Trap Server started in new console."}
    except Exception as e:
        return {"error": str(e)}
```

### `_launch_wallet_poc`
```python
def _launch_wallet_poc(self):
    """Launches the local Phishing POC server."""
    print("   ⚔️ [Offensive]: Launching Xverse 'Signing-Bypass' Simulation...")
    script_path = r"d:\AGL\agl_targets\xverse_poc\AGL_POC_SERVER.py"
    try:
         subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
         return {"status": "POC Server Running", "url": "http://localhost:8080/index.html"}
    except Exception as e:
         return {"error": str(e)}
```

---

## 3. CTF Tools (حل مسابقات)

### `_orchestrate_ctf_solve`
**ملاحظة:** هذه الدالة ~375 سطر. تستخدم Selenium لفتح متصفح Edge وحل تحديات 1Password CTF.
تتضمن: XSS Polyglot، SQL Injection، IDOR Fuzzing، API Discovery.
**لا علاقة لها بتحليل العقود الذكية.**

```python
def _orchestrate_ctf_solve(self, target: str) -> Dict[str, Any]:
    """Full Auto-CTF Sequence for Crypto.com Challenge."""
    # [~375 lines of Selenium-based CTF solving]
    # Phase 1: Deep Scanning (calls _scan_ports, _analyze_headers)
    # Phase 2: AI & Resonance Analysis (calls _ai_analyze_target, _resonance_select_exploit)
    # Phase 3: Strategic Planning (calls _generate_attack_plan)
    # Phase 4: Active Engagement via Selenium Edge:
    #   - Asset Discovery (robots.txt, scripts, API paths)
    #   - Regex extraction of /api/v* endpoints
    #   - IDOR/Admin parameter fuzzing
    #   - SQL Injection probe (7 payloads × 5 params)
    #   - XSS Polyglot injection (4 payloads)
    #   - General mop-up sweep
    # Returns: MISSION_COMPLETE/MISSION_FAILED with captured flag
```

> **الكود الكامل لم يُنسخ هنا لأنه ~375 سطر.**
> **المرجع الأصلي:** offensive_security.py lines 2029-2403 (قبل النقل)

---

## 4. process_task Routes التي تم حذفها

```python
# تم حذف هذه المسارات من process_task:
if task == "port_scan":
    return self._scan_ports(target)
elif task == "header_analysis":
    return self._analyze_headers(target)
elif task == "banner_grab":
    return self._grab_banner(target)
elif task == "1password_ctf_solve":
    return self._orchestrate_ctf_solve(target)
elif task == "launch_xverse_poc":
    return self._launch_wallet_poc()
elif task == "launch_figma_trap":
    return self._launch_figma_redirect_server()
```

---

## 📝 للاستعادة لاحقاً
إذا أردت استعادة أي من هذه الدوال:
1. أنشئ ملف منفصل (مثل `recon_tools.py`)
2. أنشئ class جديد (مثل `ReconEngine`)
3. انقل الدوال إليه
4. سجّله في `__init__.py` بشكل مستقل عن `OffensiveSecurityEngine`
