import json
import os
import time
from typing import List, Dict, Any

class WebSearchEngine:
    """
    Ù…Ø­Ø±Ùƒ Ø¨Ø­Ø« ÙˆÙŠØ¨ (Ù…Ø­Ø§ÙƒÙŠ) Ù„Ù„Ù†Ø¸Ø§Ù….
    ÙÙŠ Ø¨ÙŠØ¦Ø© Ù…Ø¹Ø²ÙˆÙ„Ø© (Air-gapped)ØŒ ÙŠÙ‚ÙˆÙ… Ù‡Ø°Ø§ Ø§Ù„Ù…Ø­Ø±Ùƒ Ø¨ØªÙˆÙ„ÙŠØ¯ Ù†ØªØ§Ø¦Ø¬ Ø¨Ø­Ø« ÙˆØ§Ù‚Ø¹ÙŠØ©
    Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ù†Ù…ÙˆØ°Ø¬ Ø§Ù„Ù„ØºÙˆÙŠ Ù„Ù…Ø­Ø§ÙƒØ§Ø© Ø§Ù„ÙˆØµÙˆÙ„ Ø¥Ù„Ù‰ Ø§Ù„Ù…Ø¹Ù„ÙˆÙ…Ø§Øª.
    """
    
    def __init__(self):
        self.name = "Web_Search_Engine"
        self.provider = os.getenv('AGL_LLM_PROVIDER', 'ollama')
        self.model = os.getenv('AGL_LLM_MODEL', 'qwen2.5:7b-instruct')
        
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        ØªÙ†ÙÙŠØ° Ø¨Ø­Ø« Ø¹Ù† Ø§Ù„Ø§Ø³ØªØ¹Ù„Ø§Ù… Ø§Ù„Ù…Ø¹Ø·Ù‰.
        ÙŠØ­Ø§ÙˆÙ„ Ø§Ø³ØªØ®Ø¯Ø§Ù… DuckDuckGo (Ù…ÙƒØªØ¨Ø© Ø£Ùˆ Ø·Ù„Ø¨ Ù…Ø¨Ø§Ø´Ø±)ØŒ Ø«Ù… ÙŠØ¹ÙˆØ¯ Ù„Ù„Ù…Ø­Ø§ÙƒØ§Ø©.
        """
        print(f"ðŸŒ [WebSearch] Searching for: {query}...")
        
        # 1. Try Real Search (Library)
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                if results:
                    print(f"   âœ… Real search successful (Library) ({len(results)} results)")
                    clean_results = []
                    for r in results:
                        clean_results.append({
                            "title": r.get('title', ''),
                            "snippet": r.get('body', ''),
                            "url": r.get('href', '')
                        })
                    return clean_results
        except ImportError:
            pass # Library not installed, try manual fallback
        except Exception as e:
            print(f"   âš ï¸ Library search failed: {e}")

        # 2. Try Real Search (Manual Request Fallback)
        try:
            import urllib.request
            import urllib.parse
            import re
            
            # Simple HTML search on DuckDuckGo Lite
            encoded_query = urllib.parse.quote(query)
            url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                
            # Simple regex to extract results (Fragile but works for basic needs)
            # Looking for table rows with results
            # This is a very basic scraper for the Lite version
            results = []
            links = re.findall(r'<a class="result-link" href="(.*?)">(.*?)</a>', html)
            snippets = re.findall(r'<td class="result-snippet">(.*?)</td>', html)
            
            for i in range(min(len(links), num_results)):
                link_url = links[i][0]
                title = links[i][1]
                snippet = snippets[i] if i < len(snippets) else "No snippet available"
                
                # Clean up HTML entities
                title = re.sub(r'<.*?>', '', title)
                snippet = re.sub(r'<.*?>', '', snippet)
                
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": link_url
                })
                
            if results:
                print(f"   âœ… Real search successful (Manual Fallback) ({len(results)} results)")
                return results
                
        except Exception as e:
            print(f"   âš ï¸ Manual search fallback failed: {e}")

        # 3. Fallback to Internal Knowledge (User Requested)
        print(f"   ðŸ§  Retrieving information from Internal Model Knowledge for: {query}")
        results = self._retrieve_internal_knowledge(query, num_results)
        return results

    def _retrieve_internal_knowledge(self, query: str, count: int) -> List[Dict[str, str]]:
        """
        Retrieves information directly from the LLM's training data instead of simulating fake search results.
        """
        from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
        
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
            import re
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
            print(f"âš ï¸ Internal knowledge retrieval failed: {e}")
            # Fallback results
            return [
                {
                    "title": f"Internal Knowledge: {query}",
                    "snippet": f"I have general knowledge about {query} in my training data, but I couldn't structure it into a list right now.",
                    "url": "Internal_Memory"
                }
            ]

    def process_task(self, task_data: Any) -> Dict[str, Any]:
        """
        ÙˆØ§Ø¬Ù‡Ø© Ù…ÙˆØ­Ø¯Ø© Ù„Ù„Ù…Ø­Ø±Ùƒ
        """
        query = task_data if isinstance(task_data, str) else task_data.get('query', '')
        if not query:
            return {"error": "No query provided"}
            
        results = self.search(query)
        return {
            "query": query,
            "results": results,
            "source": "Simulated_Web_Search",
            "timestamp": time.time()
        }

