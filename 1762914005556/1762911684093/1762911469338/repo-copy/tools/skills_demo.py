"""Demo: LLM suggests a tool call, orchestrator runs it, then LLM finalizes.

This demo shows the flow described by the user:
  1. Ask LLM to output a JSON tool decision (only JSON).
  2. Parse the JSON, validate and run the tool via ToolRunner.
  3. Send the tool result back to the LLM to produce a final answer.

Run with:
  $env:PYTHONPATH='D:\AGL'; py -3 tools\skills_demo.py
"""
import json
import os
from Core_Engines.turn_contract import make_turn
from Core_Engines.Ollama_KnowledgeEngine import OllamaKnowledgeEngine
from Core_Engines.skills_registry import ToolRunner


def _exp_algebra_solve(args):
    expr = args.get("expr", "")
    # Very small mock: handle (e^(x))' -> e^x
    if "(e^(x))'" in expr or "(e^x)'" in expr:
        return {"value": None, "steps": "d/dx e^x = e^x"}
    # fallback: echo
    return {"value": None, "steps": f"cannot_solve:{expr}"}


def _rag_search(args):
    q = args.get("query", "")
    k = int(args.get("k", 3))
    # mock chunks
    chunks = [{"id": f"c{i}", "text": f"chunk about {q} #{i}"} for i in range(1, k+1)]
    return {"chunks": chunks}


def _safety_review(args):
    text = args.get("text", "")
    flags = [] if len(text) < 500 else ["long_text"]
    return {"passed": len(flags) == 0, "flags": flags}


def main():
    os.environ.setdefault('AGL_OLLAMA_KB_CACHE_ENABLE', '0')
    eng = OllamaKnowledgeEngine()

    # Tool runner and register mocks
    tr = ToolRunner()
    tr.register('exp_algebra.solve', _exp_algebra_solve)
    tr.register('rag.search', _rag_search)
    tr.register('safety.review', _safety_review)

    user_question = "أوجد مشتقة (e^(x))' واذكر خطوات الحل"

    # Ask LLM to propose a tool call in JSON only
    prompt = (
        "أنت أداة تنسيق: أعِد فقط JSON وحده دون شرح.\n"
        "الهدف: حدد أي أداة من القائمة التالية تستدعيها لحل السؤال، واكتب اسم الأداة ووسائطها.\n"
        "TOOLS: [\"exp_algebra.solve\", \"rag.search\", \"safety.review\"]\n"
        "ارجو إخراج JSON مثل: {\"tool\":\"exp_algebra.solve\", \"args\":{\"expr\":\"(e^(x))'\"}}\n"
        f"السؤال: {user_question}\n"
    )

    turn = make_turn(user_question)
    # Use engine.ask to get suggestion
    res_turn = eng.ask(prompt)
    # Extract raw engine_result from working.calls (last one)
    calls = res_turn.get('working', {}).get('calls', [])
    engine_result = calls[-1]['engine_result'] if calls else {}
    suggestion_text = engine_result.get('text') if isinstance(engine_result, dict) else ''

    print("LLM suggestion (raw):", suggestion_text)

    # Parse JSON
    try:
        suggestion = json.loads(suggestion_text)
        tool = suggestion.get('tool')
        args = suggestion.get('args', {})
    except Exception as e:
        print("Failed to parse suggestion JSON:", e)
        return

    # Execute tool
    tool_res = tr.run(tool, args)
    print("Tool execution result:", tool_res)

    # Send tool result back to LLM to craft final answer
    followup = (
        "أعد الآن إجابة نهائية مُنسقة للمستخدم بالاعتماد على نتيجة الأداة التالية (JSON):\n"
        + json.dumps({"tool": tool, "args": args, "result": tool_res}, ensure_ascii=False)
    )
    final_turn = eng.ask(followup)
    final_calls = final_turn.get('working', {}).get('calls', [])
    final_engine_result = final_calls[-1]['engine_result'] if final_calls else {}
    print("Final LLM answer:", final_engine_result.get('text'))


if __name__ == '__main__':
    main()
