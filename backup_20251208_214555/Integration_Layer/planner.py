# Planner skeleton: register and execute simple tools. This is an extensible hook for multi-step tasks.
from typing import Any, Callable, Dict, List

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]):
        self.tools[name] = func

    def run(self, name: str, *args, **kwargs):
        if name not in self.tools:
            raise KeyError(f"tool {name} not registered")
        return self.tools[name](*args, **kwargs)

# Example stubs
def web_search_stub(query: str, limit: int = 3):
    return [{'title': 'stub', 'snippet': f'Stub results for: {query}', 'url': 'http://example.com'}]

def run_code_stub(code: str):
    try:
        # Dangerous in production: do not execute untrusted code
        loc = {}
        exec(code, {}, loc)
        return {'ok': True, 'result': loc}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

_default_registry = ToolRegistry()
_default_registry.register('web_search', web_search_stub)
_default_registry.register('run_code', run_code_stub)

def plan_and_execute(plan: List[Dict[str, Any]]):
    # Plan is list of {tool:..., args:..., kwargs:...}
    results = []
    for step in plan:
        tool = step.get('tool')
        args = step.get('args', [])
        kwargs = step.get('kwargs', {})
        res = _default_registry.run(tool, *args, **kwargs) # type: ignore
        results.append({'tool': tool, 'result': res})
    return results
