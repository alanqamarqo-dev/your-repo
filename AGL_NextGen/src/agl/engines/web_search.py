import json
import os
import time
import re
import urllib.parse
from typing import List, Dict, Any

# Check available libraries
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQ_BS4 = True
except ImportError:
    HAS_REQ_BS4 = False

class WebSearchEngine:
    """
    AGL Web Search Engine (Hybrid: Real + Mock).
    
    Capabilities:
    1. Real Internet Search (Priority): Uses Google/DDG via Requests+BS4 (Robust Scraper).
    2. Fallback Mock: Uses Internal LLM Knowledge if offline.
    
    Status: UPGRADED to Live Internet (Requests + BeautifulSoup).
    """
    
    def __init__(self):
        self.name = "Web_Search_Engine"
        self.provider = os.getenv('AGL_LLM_PROVIDER', 'ollama')
        self.model = os.getenv('AGL_LLM_MODEL', 'qwen2.5:7b-instruct')
        self.live_mode = True 
        self.session = None
        if HAS_REQ_BS4:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })

    def set_live_mode(self, enabled: bool):
        """
        Sets the live mode for the web search engine.
        """
        self.live_mode = enabled
        mode_str = "ENABLED" if enabled else "DISABLED"
        print(f"[{self.name}] LIVE KNOWLEDGE MODE {mode_str}.")
        
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Executes a real web search using available providers.
        """
        print(f"🌍 [WebSearch] Searching for: {query}...")
        
        # 1. Try DuckDuckGo via Requests/BS4 (HTML) - Most Reliable/Least Blocked
        if HAS_REQ_BS4:
            try:
                # print("   🔌 Attempting DuckDuckGo HTML Search...")
                url = "https://html.duckduckgo.com/html/"
                data = {'q': query}
                
                resp = self.session.post(url, data=data, timeout=10)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = []
                    
                    for link in soup.find_all('a', class_='result__a', limit=num_results):
                        title = link.get_text()
                        url_res = link['href']
                        
                        # Find snippet (next sibling usually)
                        snippet_div = link.find_next(class_='result__snippet')
                        snippet = snippet_div.get_text() if snippet_div else "No snippet"
                        
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": url_res
                        })
                        
                    if results:
                        print(f"   ✅ Real search successful (DuckDuckGo/BS4) ({len(results)} results)")
                        return results
            except Exception as e:
                print(f"   ⚠️ DDG BS4 failed: {e}")
                pass

        # 2. Try Google via Requests/BS4
        if HAS_REQ_BS4:
            try:
                # print("   🔌 Attempting Google HTML Search...")
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={num_results+5}" 
                
                resp = self.session.get(search_url, timeout=10)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')

                    results = []
                    
                    # Modern Google HTML is tricky, try standard classes
                    result_divs = soup.find_all('div', class_='g')
                    
                    for div in result_divs:
                        if len(results) >= num_results:
                            break
                            
                        a_tag = div.find('a')
                        if not a_tag: continue
                        
                        link = a_tag.get('href')
                        if not link or link.startswith('/search'): continue
                        
                        h3 = a_tag.find('h3')
                        title = h3.get_text() if h3 else "Google Result"
                        
                        snippet = "No description available"
                        # Try common snippet classes
                        for snip_class in ['VwiC3b', 'yXK7lf', 'ITZIwc']:
                            snip_div = div.find('div', class_=snip_class)
                            if snip_div:
                                snippet = snip_div.get_text()
                                break

                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link
                        })
                        
                    if results:
                        print(f"   ✅ Real search successful (Google/BS4) ({len(results)} results)")
                        return results
            except Exception as e:
                print(f"   ⚠️ Google BS4 failed: {e}")
                pass

        # 3. Fallback to System Shell Bridge (PowerShell)
        try:
                # print("   Trying System Shell Bridge (PowerShell - DDG Lite)...")
                import subprocess
                
                # Use DuckDuckGo Lite which has cleaner HTML
                encoded_query = urllib.parse.quote(query)
                target_url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
                
                # Use PowerShell to fetch, silencing progress
                ps_command = f'$ProgressPreference = "SilentlyContinue"; Invoke-WebRequest -Uri "{target_url}" -UseBasicParsing -Headers @{{ "User-Agent" = "Mozilla/5.0" }} | Select-Object -ExpandProperty Content'
                
                # Run PowerShell command
                result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0 and result.stdout:
                    html = result.stdout
                    results = []
                    # Parse DDG Lite HTML
                    links = re.findall(r'<a class="result-link" href="(.*?)">(.*?)</a>', html)
                    snippets = re.findall(r'<td class="result-snippet">(.*?)</td>', html)

                    for i in range(min(len(links), num_results)):
                        clean_link = links[i][0]
                        clean_title = re.sub(r'<.*?>', '', links[i][1])
                        clean_snippet = re.sub(r'<.*?>', '', snippets[i]) if i < len(snippets) else "Live Result"
                        
                        results.append({
                            "title": clean_title,
                            "snippet": clean_snippet,
                            "url": clean_link
                        })
                            
                    if results:
                        print(f"   ✅ Real search successful (System Bridge / DDG) ({len(results)} results)")
                        return results
        except Exception as e:
             pass

        # 4. Fallback to Internal Knowledge (User Requested)
        print(f"   🧠 [OFFLINE] Retrieved from Internal Model Knowledge for: {query}")
        print("   ⚠️ No live internet connection methods succeeded. Using internal simulation.")
        results = self._retrieve_internal_knowledge(query, num_results)
        return results

    def _retrieve_internal_knowledge(self, query: str, count: int) -> List[Dict[str, str]]:
        """
        Retrieves information directly from the LLM's training data instead of simulating fake search results.
        """
        # Try importing from known location, handle robustly
        try:
            from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
        except ImportError:
            try:
                # Fallback path if running from different context
                import sys
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
            except ImportError:
                print("   ❌ Critical: Could not import LLM engine.")
                return []

        prompt = f"""
        You are the system's internal knowledge base.
        The user is asking about: "{query}".
        Internet access is restricted, so you must provide the best information you have from your training data.
        
        Provide {count} distinct, accurate, and useful facts or insights about this topic.
        
        Format the output as a JSON list of objects, where each object has:
        - "title": A clear title for the specific insight.
        - "snippet": A comprehensive explanation (3-4 sentences) containing actual information.
        - "url": "Internal_Memory"
        
        Return ONLY the JSON list.
        """
        
        try:
            response = ask_with_deep_thinking(prompt, model=self.model)
            # Clean up response to ensure valid JSON
            json_str = response.strip()
            
            # Remove any thinking blocks if present (e.g. <think>...</think>)
            json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL).strip()
            
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Attempt to find list start/end if extra text exists
            start_idx = json_str.find('[')
            end_idx = json_str.rfind(']')
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx+1]
                
            results = json.loads(json_str)
            return results[:count]
        except Exception as e:
            print(f"⚠️ Internal knowledge retrieval failed: {e}")
            # Fallback results
            return [
                {
                    "title": f"Internal Knowledge: {query}",
                    "snippet": f"I have general knowledge about {query} but couldn't retrieve structured data.",
                    "url": "Internal_Memory"
                }
            ]

    def process_task(self, task_data: Any) -> Dict[str, Any]:
        """
        Unified engine interface.
        """
        query = task_data if isinstance(task_data, str) else task_data.get('query', '')
        if not query:
            return {"error": "No query provided"}
            
        results = self.search(query)
        return {
            "query": query,
            "results": results,
            "source": "Hybrid_Web_Search",
            "timestamp": time.time()
        }
