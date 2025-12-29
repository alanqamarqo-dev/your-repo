from Safety_Control.Dialogue_Safety import guard
from Integration_Layer.Conversation_Manager import append_turn, create_session, last_turn


def route(task: str, law: str | None, kv: dict, session_id: str | None = None) -> dict:
    # Lazy import to avoid heavy startup cost
    if task is None:
        return {"ok": False, "message": "لم تُحدد نية السؤال."}

    # New: explicit solve_ohm task
    if task == "solve_ohm" or (task == "infer" and law == "ohm"):
        # Expect kv keys maybe as 'V','I','R' floats
        V = kv.get("V")
        I = kv.get("I")
        R = kv.get("R")

        # If any values are strings, try to normalize to float
        def _to_float(x):
            try:
                return float(x)
            except Exception:
                return None

        V = _to_float(V) if V is not None else None
        I = _to_float(I) if I is not None else None
        R = _to_float(R) if R is not None else None

        # Compute missing variable when two provided
        try:
            if V is None and I is not None and R is not None:
                V_calc = I * R
                return guard({"ok": True, "result": f"V ≈ {V_calc:.4f} V", "confidence": 0.98, "units_ok": True})
            if I is None and V is not None and R is not None:
                if R == 0:
                    return {"ok": False, "message": "المقاومة صفرية، لا يمكن القسمة على صفر."}
                I_calc = V / R
                return guard({"ok": True, "result": f"I ≈ {I_calc:.4f} A", "confidence": 0.98, "units_ok": True})
            if R is None and V is not None and I is not None:
                if I == 0:
                    return {"ok": False, "message": "التيار صفر، لا يمكن القسمة على صفر."}
                R_calc = V / I
                return guard({"ok": True, "result": f"R ≈ {R_calc:.4f} Ω", "confidence": 0.98, "units_ok": True})
        except Exception:
            return {"ok": False, "message": "حدث خطأ أثناء الحساب. تأكد من القيم المدخلة."}

        # Missing values -> ask follow-up
        if session_id:
            prev = last_turn(session_id)
            follow = "من فضلك قدم قيمتين من V, I, أو R." if not (prev and prev.get('agent')) else "هل أستخدم نفس القيم السابقة؟"
            resp = {"ok": False, "message": "بحاجة لقيمتين من (V, I, R) لإتمام حل قانون أوم.", "follow_up": follow}
            append_turn(session_id, f"ask_for_values", resp)
            return resp

        return {"ok": False, "message": "بحاجة لقيمتين من (V, I, R) لإتمام حل قانون أوم."}

    if task == "infer" and law == "rc_step":
        return guard({"ok": False, "message": "دعم RC مبسّط الآن—أرسل (t) ومنحنى أو استخدم تقرير النظام."})

    if task == "discover":
        try:
            from Self_Improvement.Self_Engineer import SelfEngineer # type: ignore
            se = SelfEngineer()
            smoke = se.quick_smoke()
            win = smoke.get("winner", {})
            expr = win.get("candidate", {}).get("expr", "unknown")
            return guard({"ok": True, "result": f"اقتراح أولي: {expr}", "confidence": 0.6})
        except Exception:
            return guard({"ok": False, "message": "تعذر تشغيل Self-Engineer حالياً."})

    if task == "report":
        return {"ok": True, "result": "التقارير جاهزة تحت /reports؛ افتح full_system_report.html", "confidence": 1.0}

    if task == "explain":
        return {"ok": True, "result": "تم تعزيز التفسير داخل التقارير، ويدعم تلخيصًا سريعًا لاحقًا.", "confidence": 0.9}

    return {"ok": False, "message": "لم تُفهم المهمة المطلوبة."}


def route_for_task(task_name: str) -> list:
    """Explicit routing table for AS test harness.

    Returns a list of pipeline step names in order.
    """
    if task_name == "as_test_1_context":
        return ["chat_llm", "self_check", "format_md"]
    elif task_name == "as_test_2_planning":
        return ["planner", "chat_llm", "self_eval", "format_md"]
    elif task_name == "as_test_3_transfer":
        return ["chat_llm", "self_analysis", "format_md"]
    elif task_name == "as_test_4_creative":
        return ["idea_gen", "chat_llm", "self_eval", "format_md"]
    elif task_name == "as_test_5_strategy":
        return ["planner", "chat_llm", "self_eval", "format_md"]
    else:
        return ["chat_llm", "format_md"]
