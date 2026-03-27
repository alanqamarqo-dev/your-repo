import os
import sys
import requests
import json
import time
import socket
from urllib.parse import urlparse

def print_status(step, status, details=""):
    icon = "✅" if status == "OK" else "❌" if status == "FAIL" else "⚠️"
    print(f"{icon} [{step}]: {status} {details}")

def check_environment():
    print("\n🔍 1. Environment Variables Check:")
    base_url = os.getenv('AGL_LLM_BASEURL', 'http://localhost:11434')
    model = os.getenv('AGL_LLM_MODEL', 'qwen2.5:7b-instruct')
    provider = os.getenv('AGL_LLM_PROVIDER', 'ollama')
    
    print(f"   - AGL_LLM_BASEURL: {base_url}")
    print(f"   - AGL_LLM_MODEL: {model}")
    print(f"   - AGL_LLM_PROVIDER: {provider}")
    
    return base_url, model

def check_server_reachability(url):
    print("\n📡 2. Server Reachability Check:")
    parsed = urlparse(url)
    host = parsed.hostname or 'localhost'
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    
    print(f"   - Pinging {host}:{port}...")
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        print_status("TCP Connection", "OK", f"Connected to {host}:{port}")
        return True
    except socket.timeout:
        print_status("TCP Connection", "FAIL", "Timeout (Server is down or blocked)")
        return False
    except ConnectionRefusedError:
        print_status("TCP Connection", "FAIL", "Connection Refused (Ollama not running?)")
        return False
    except Exception as e:
        print_status("TCP Connection", "FAIL", str(e))
        return False

def check_api_endpoint(base_url):
    print("\n🔌 3. API Endpoint Check:")
    # Try /api/tags or /api/version
    endpoints = ['/api/tags', '/api/version', '/']
    
    for ep in endpoints:
        full_url = base_url.rstrip('/') + ep
        try:
            response = requests.get(full_url, timeout=5)
            if response.status_code == 200:
                print_status(f"GET {ep}", "OK", f"Status 200")
                return True
            else:
                print_status(f"GET {ep}", "WARN", f"Status {response.status_code}")
        except Exception as e:
            print_status(f"GET {ep}", "FAIL", str(e))
            
    return False

def check_model_availability(base_url, model_name):
    print("\n📦 4. Model Availability Check:")
    url = base_url.rstrip('/') + '/api/tags'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            # Check for exact or partial match
            found = False
            for m in models:
                if model_name in m:
                    found = True
                    print_status("Model Search", "OK", f"Found '{m}' matching '{model_name}'")
                    break
            
            if not found:
                print_status("Model Search", "FAIL", f"Model '{model_name}' NOT found in: {models}")
                return False
            return True
        else:
            print_status("List Models", "FAIL", f"Could not list models. Status: {response.status_code}")
            return False
    except Exception as e:
        print_status("List Models", "FAIL", str(e))
        return False

def check_generation(base_url, model_name):
    print("\n🧠 5. Generation Capability Check:")
    url = base_url.rstrip('/') + '/api/generate'
    payload = {
        "model": model_name,
        "prompt": "Say 'Connected' if you hear me.",
        "stream": False,
        "options": {"num_predict": 10}
    }
    
    start_time = time.time()
    try:
        print(f"   - Sending request to {url}...")
        response = requests.post(url, json=payload, timeout=30)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json()
                text = data.get('response', '')
                print_status("Generation", "OK", f"Response in {duration:.2f}s: '{text.strip()}'")
                return True
            except json.JSONDecodeError:
                print_status("Generation", "FAIL", "Invalid JSON response")
                print(f"   Raw response: {response.text[:100]}")
                return False
        else:
            print_status("Generation", "FAIL", f"HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_status("Generation", "FAIL", "Request Timed Out (>30s)")
        return False
    except requests.exceptions.ConnectionError:
        print_status("Generation", "FAIL", "Connection Error during generation")
        return False
    except Exception as e:
        print_status("Generation", "FAIL", str(e))
        return False

if __name__ == "__main__":
    print("🕵️ STARTING LLM CONNECTIVITY DIAGNOSIS...")
    base_url, model = check_environment()
    
    if check_server_reachability(base_url):
        if check_api_endpoint(base_url):
            if check_model_availability(base_url, model):
                check_generation(base_url, model)
            else:
                print("\n❌ DIAGNOSIS: Server is running, but the MODEL is missing.")
                print("   Action: Run `ollama pull <model_name>`")
        else:
            print("\n❌ DIAGNOSIS: Server is reachable (TCP), but API is not responding correctly.")
            print("   Action: Check if it's actually Ollama or another service.")
    else:
        print("\n❌ DIAGNOSIS: Cannot connect to server.")
        print("   Action: Ensure Ollama is running (`ollama serve`) and port is correct.")
