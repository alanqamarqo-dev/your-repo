# config/engine_preference.py

# خريطة التوجيه الذكي: (الاسم العام المطلق) -> (الاسم المحدد الأقوى الموجود في النظام)
ENGINE_MAPPING = {
    # --- المسار الكمي ---
    "QuantumCore": "AdvancedQuantumEngine",
    "QuantumSolver": "QuantumAlgorithmEngine",

    # --- المسار العلمي والرياضي ---
    "MathematicalBrain": "MathematicalBrain",
    "CalculusEngine": "AdvancedLinearAlgebra",
    "LogicEngine": "AutomatedTheoremProver",

    # --- المسار الإبداعي والاستراتيجي ---
    "CreativeInnovation": "CreativeInnovationEngine",
    "StrategicThinking": "AdvancedMetaReasonerEngine",

    # --- المحاكاة والهندسة ---
    "SimulationEngine": "IntegratedSimulationEngine",
    "CodeGenerator": "AdvancedCodeGenerator",

    # --- الذكاء اللغوي ---
    "LLM": "HostedLLM"
}


def get_preferred_engine(requested_name: str) -> str:
    """Return preferred engine name for a requested name, or original name if no mapping."""
    return ENGINE_MAPPING.get(requested_name, requested_name)
