import subprocess
import urllib.parse
import re
import os

def run_search_bridge_debug(query='current price of bitcoin today'):
    encoded_query = urllib.parse.quote(query)
    # Use gbv=1 for legacy
    url = f'https://www.google.com/search?q={encoded_query}&num=10&gbv=1'
    print(f'DEBUG: Requesting {url}')
    
    ps_file = 'd:\\AGL\\temp_search_debug.ps1'
    # Use simple string for the command to avoid f-string complexity or escaping issues if possible
    # but we need the url.
    ps_command = f"""
$url = "{url}"
try {{
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $headers = @{{
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        "Referer" = "https://www.google.com/"
    }}
    $response = Invoke-WebRequest -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 15
    Write-Output $response.Content
}} catch {{
    Write-Error $_.Exception.Message
}}
"""
    
    with open(ps_file, 'w') as f:
        f.write(ps_command)
        
    try:
        result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_file], capture_output=True, text=True, timeout=30)
        print(f'Return Code: {result.returncode}')
        
        content = result.stdout
        if len(content) > 100:
            with open('d:\\AGL\\test_google_gbv.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print('Dumped HTML.')
            
            # Simple Regex for gbv=1
            # Links look like: <a href="/url?q=http..."
            urls = re.findall(r'/url\?q=(https?://[^"&]+)', content)
            print(f'Found {len(urls)} Raw URLs')
            
            valid_count = 0
            for u in urls:
                if "google.com" not in u:
                    print(f'- {u}')
                    valid_count += 1
                    if valid_count >= 5: break
        else:
            print('Content too short.')
            print(result.stderr)
            
    except Exception as e:
        print(e)
    finally:
        if os.path.exists(ps_file):
            os.remove(ps_file)

if __name__ == '__main__':
    run_search_bridge_debug()
