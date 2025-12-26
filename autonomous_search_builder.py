import sys
import os
import urllib.request
import time
import json

# Add repo-copy to path explicitly
repo_path = os.path.join(os.getcwd(), 'repo-copy')
if repo_path not in sys.path:
    sys.path.append(repo_path)

try:
    from Core_Engines.Creative_Innovation import CreativeInnovation
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Sys Path: {sys.path}")
    sys.exit(1)

def check_connectivity():
    targets = [
        ("https://lite.duckduckgo.com", "DuckDuckGo Lite"),
        ("https://www.google.com", "Google"),
        ("https://www.bing.com", "Bing")
    ]
    
    results = {}
    print("🕵️ [Reconnaissance] Checking network connectivity (Python & PowerShell)...")
    
    import subprocess
    
    for url, name in targets:
        # 1. Python Check
        py_status = "blocked"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.getcode() == 200:
                    py_status = "accessible"
        except Exception:
            pass
            
        # 2. PowerShell Check (The Innovation!)
        ps_status = "blocked"
        try:
            cmd = ["powershell", "-Command", f"(Invoke-WebRequest -Uri '{url}' -UseBasicParsing -TimeoutSec 3).StatusCode"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if "200" in result.stdout:
                ps_status = "accessible"
        except Exception:
            pass
            
        print(f"   Target: {name} | Python: {py_status} | PowerShell: {ps_status}")
        
        if py_status == "accessible":
            results[name] = {"status": "accessible", "method": "python", "url": url}
        elif ps_status == "accessible":
            results[name] = {"status": "accessible", "method": "powershell", "url": url}
        else:
            results[name] = {"status": "blocked", "error": "Both methods failed"}
            
    return results

def build_search_tool():
    # 1. Reconnaissance
    connectivity = check_connectivity()
    
    # 2. Innovation
    print("\n🧠 [Creative Innovation] Designing custom search solution based on environment...")
    innovator = CreativeInnovation()
    
    accessible_engines = [name for name, data in connectivity.items() if data['status'] == 'accessible']
    
    if not accessible_engines:
        print("⚠️ CRITICAL: No search engines are directly accessible via standard HTTP.")
        print("   Attempting to design a fallback strategy (e.g., using specific API endpoints or alternative proxies).")
    
    prompt_context = f"""
    Current Network Environment:
    {json.dumps(connectivity, indent=2)}
    
    Constraints:
    - Cannot install new pip packages (must use standard library: urllib, json, re, html).
    - Must be robust against simple HTML parsing errors.
    - Goal: Create a Python function `def custom_search(query):` that returns a list of dicts with title, link, snippet.
    """
    
    task = {
        "query": "Write a complete, error-handled Python script named 'custom_search_tool.py' that implements a search function using the accessible engines found. Use 'urllib.request' and regex/string parsing. Do not use 'requests' or 'BeautifulSoup'. The code should be self-contained.",
        "context": prompt_context
    }
    
    result = innovator.process_task(task)
    
    if result['status'] == 'success':
        generated_content = result['output']
        
        # Extract code block
        import re
        code_match = re.search(r'```python(.*?)```', generated_content, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
        else:
            code = generated_content # Fallback if no blocks
            
        # Save the tool
        with open('custom_search_tool.py', 'w', encoding='utf-8') as f:
            f.write(code)
            
        print("\n🔨 [Construction] 'custom_search_tool.py' has been generated.")
        print("   Content preview:")
        print("\n".join(code.split('\n')[:5]) + "\n...")
        
        return True
    else:
        print("❌ Innovation Engine failed to generate a solution.")
        return False

if __name__ == "__main__":
    print("🚀 Starting Autonomous Search Tool Builder...")
    success = build_search_tool()
    if success:
        print("\n🧪 [Testing] Verifying the new tool...")
        try:
            import custom_search_tool # type: ignore
            if hasattr(custom_search_tool, 'custom_search'):
                print("   Running search for 'AGI latest research'...")
                results = custom_search_tool.custom_search("AGI latest research")
                print(f"   Found {len(results)} results.")
                for r in results:
                    print(f"   - {r.get('title', 'No Title')}: {r.get('url', 'No URL')}")
            else:
                print("   ❌ Generated file does not contain 'custom_search' function.")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
