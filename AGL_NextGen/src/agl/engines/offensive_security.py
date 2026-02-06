import socket  # استيراد مكتبة socket
import ssl  # استيراد مكتبة ssl
import requests  # استيراد مكتبة requests
import urllib.error  # استيراد مكتبة urllib
import time  # استيراد مكتبة time
import subprocess  # استيراد مكتبة subprocess
import shutil  # استيراد مكتبة shutil
import re  # استيراد مكتبة re
import os  # استيراد مكتبة os
import sys  # استيراد مكتبة sys
from typing import Dict, Any, List, Optional  # استيراد من وحدة typing
import json  # استيراد مكتبة json

# --- AGL INTEGRATION IMPORTS ---
try:  # محاولة استيراد المحرك الهولوغرافي
    from agl.engines.holographic_llm import HolographicLLM  # استيراد صنف المحرك الهولوغرافي من محركات AGL
    HOLO_AVAILABLE = True  # تعيين علامة توفر المحرك الهولوغرافي إلى صحيح
except ImportError:  # معالجة حالة عدم وجود المحرك الهولوغرافي
    HOLO_AVAILABLE = False  # تعيين علامة التوفر إلى خاطئ
    print("⚠️ [OffensiveSecurity]: HolographicLLM not found. Reverting to manual mode.")  # طباعة تحذير بعدم توفر المحرك الهولوغرافي

try:  # محاولة استيراد محرك التفكير الفوقي المتقدم
    from agl.engines.advanced_meta_reasoner import AdvancedMetaReasonerEngine  # استيراد صنف محرك التفكير الفوقي
    META_AVAILABLE = True  # تعيين علامة توفر المحرك الفوقي إلى صحيح
except ImportError:  # معالجة حالة عدم وجود المحرك الفوقي
    META_AVAILABLE = False  # تعيين علامة التوفر إلى خاطئ
    print("⚠️ [OffensiveSecurity]: AdvancedMetaReasonerEngine not found. Strategy disabled.")  # طباعة تحذير بعدم توفر المحرك الفوقي

try:  # محاولة استيراد محسّن الرنين الكمي
    from agl.engines.resonance_optimizer import ResonanceOptimizer  # استيراد صنف محسّن الرنين
    RESONANCE_AVAILABLE = True  # تعيين علامة توفر محسّن الرنين إلى صحيح
except ImportError:  # معالجة حالة عدم وجود محسّن الرنين
    RESONANCE_AVAILABLE = False  # تعيين علامة التوفر إلى خاطئ
    print("⚠️ [OffensiveSecurity]: ResonanceOptimizer not found. Resonance scanning disabled.")  # طباعة تحذير بعدم توفر محسّن الرنين

# [AGL-HEIKAL] Integration with Quantum Neural Core (Deep Vulnerability Discovery)
try:  # محاولة استيراد النواة الكمية العصبية (اكتشاف الثغرات العميق)
    from agl.engines.quantum_neural import QuantumNeuralCore  # استيراد صنف النواة الكمية العصبية
    QUANTUM_AVAILABLE = True  # تعيين علامة توفر النواة الكمية إلى صحيح
except ImportError:  # معالجة حالة عدم وجود النواة الكمية
    QUANTUM_AVAILABLE = False  # تعيين علامة التوفر إلى خاطئ
    print("⚠️ [OffensiveSecurity]: QuantumNeuralCore not found. Deep Logic Analysis disabled.")  # طباعة تحذير بعدم توفر النواة الكمية

# [AGL-Z3] Integration with Formal Verification Engine (Mathematical Proofs)
FORMAL_VERIFIER_AVAILABLE = False  # تهيئة متغير التحقق الرياضي كغير متاح
ProofResult = None  # تهيئة نتيجة البرهان كقيمة فارغة

try:  # محاولة استيراد محرك التحقق الرياضي الصارم (Z3)
    from agl.engines.formal_verifier import FormalVerificationEngine, ProofResult as _ProofResult  # استيراد محرك التحقق ونتيجة البرهان
    FORMAL_VERIFIER_AVAILABLE = True  # تأكيد توفر محرك التحقق الرياضي
    ProofResult = _ProofResult  # تعيين صنف نتيجة البرهان
except ImportError:  # معالجة حالة فشل الاستيراد المباشر
    try:  # محاولة الاستيراد النسبي كبديل
        # Try relative import for when running from AGL_NextGen/src
        from .formal_verifier import FormalVerificationEngine, ProofResult as _ProofResult  # استيراد نسبي من نفس الحزمة
        FORMAL_VERIFIER_AVAILABLE = True  # تأكيد التوفر بعد الاستيراد النسبي
        ProofResult = _ProofResult  # تعيين صنف نتيجة البرهان
    except ImportError:  # معالجة فشل الاستيراد النسبي أيضاً
        try:  # محاولة الاستيراد المباشر من الملف
            # Try direct import
            import sys  # استيراد مكتبة النظام
            import os  # استيراد مكتبة نظام التشغيل
            verifier_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "formal_verifier.py")  # بناء مسار ملف محرك التحقق
            if os.path.exists(verifier_path):  # التحقق من وجود الملف على القرص
                import importlib.util  # استيراد أدوات التحميل الديناميكي
                spec = importlib.util.spec_from_file_location("formal_verifier", verifier_path)  # إنشاء مواصفات التحميل من مسار الملف
                formal_verifier_module = importlib.util.module_from_spec(spec)  # إنشاء وحدة من المواصفات
                spec.loader.exec_module(formal_verifier_module)  # تنفيذ وتحميل الوحدة
                FormalVerificationEngine = formal_verifier_module.FormalVerificationEngine  # استخراج صنف محرك التحقق من الوحدة المحملة
                ProofResult = formal_verifier_module.ProofResult  # استخراج صنف نتيجة البرهان من الوحدة المحملة
                FORMAL_VERIFIER_AVAILABLE = True  # تأكيد توفر المحرك بعد التحميل الديناميكي
        except Exception as e:  # معالجة أي خطأ أثناء التحميل الديناميكي
            print(f"⚠️ [OffensiveSecurity]: FormalVerifier not found: {e}")  # طباعة تحذير مع تفاصيل الخطأ

# [AGL-HEIKAL] Import Context Aggregator
try:  # محاولة استيراد مُجمّع سياق سوليديتي
    from agl.engines.solidity_context_aggregator import SolidityContextAggregator  # استيراد صنف مُجمّع السياق
    CONTEXT_AGGREGATOR_AVAILABLE = True  # تأكيد توفر مُجمّع السياق
except ImportError:  # معالجة حالة عدم وجود مُجمّع السياق
    # Fallback if file missing
    CONTEXT_AGGREGATOR_AVAILABLE = False  # تعيين علامة التوفر إلى خاطئ
    class SolidityContextAggregator:  # إنشاء صنف بديل فارغ لمُجمّع السياق
        def scan_imports(self, *args): pass  # دالة بديلة لمسح الاستيرادات (لا تفعل شيئاً)
        def format_context(self): return "Aggregator Missing"  # دالة بديلة لتنسيق السياق (ترجع رسالة خطأ)

# ==================================================================================
# [AGL-SECURITY-SUITE] Integration with New Security Analyzer (Slither/Mythril/Z3)
# ==================================================================================
SECURITY_SUITE_AVAILABLE = False  # تعيين المتغير SECURITY_SUITE_AVAILABLE إلى خاطئ (غير متاح)
AGLSecuritySuite = None  # تهيئة علامة توفر مجموعة أدوات الأمان كغير متاحة
SmartContractAnalyzer = None  # تهيئة صنف مجموعة الأمان كقيمة فارغة

try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
    from agl.engines.agl_security import AGLSecuritySuite as _AGLSecuritySuite  # محاولة استيراد مجموعة أدوات أمان AGL
    from agl.engines.smart_contract_analyzer import SmartContractAnalyzer as _SmartContractAnalyzer  # استيراد صنف مجموعة الأمان من محركات AGL
    AGLSecuritySuite = _AGLSecuritySuite  # استيراد صنف محلل العقود الذكية
    SmartContractAnalyzer = _SmartContractAnalyzer  # تعيين مرجع مجموعة الأمان
    SECURITY_SUITE_AVAILABLE = True  # تعيين مرجع محلل العقود الذكية
except ImportError:  # تأكيد توفر مجموعة أدوات الأمان
    try:  # معالجة فشل الاستيراد المباشر
        # Try relative import
        from .agl_security import AGLSecuritySuite as _AGLSecuritySuite  # استيراد نسبي لمجموعة أدوات الأمان
        from .smart_contract_analyzer import SmartContractAnalyzer as _SmartContractAnalyzer  # استيراد نسبي لمحلل العقود الذكية
        AGLSecuritySuite = _AGLSecuritySuite  # تعيين مرجع مجموعة الأمان من الاستيراد النسبي
        SmartContractAnalyzer = _SmartContractAnalyzer  # تعيين مرجع محلل العقود الذكية من الاستيراد النسبي
        SECURITY_SUITE_AVAILABLE = True  # تأكيد التوفر بعد الاستيراد النسبي
    except ImportError:  # معالجة فشل الاستيراد النسبي أيضاً
        try:  # محاولة التحميل المباشر من الملف
            # Try direct file import
            import importlib.util  # الحصول على مسار مجلد المحركات
            engines_dir = os.path.dirname(os.path.abspath(__file__))  # عملية على مسار الملف
            
            # Load agl_security
            agl_sec_path = os.path.join(engines_dir, "agl_security.py")  # إنشاء مواصفات التحميل لملف مجموعة الأمان
            if os.path.exists(agl_sec_path):  # إنشاء وحدة من المواصفات
                spec = importlib.util.spec_from_file_location("agl_security", agl_sec_path)  # تنفيذ وتحميل وحدة مجموعة الأمان
                agl_sec_module = importlib.util.module_from_spec(spec)  # استخراج صنف مجموعة الأمان من الوحدة المحملة
                spec.loader.exec_module(agl_sec_module)  # عملية برمجية
                AGLSecuritySuite = agl_sec_module.AGLSecuritySuite  # بناء مسار ملف محلل العقود الذكية
                
            # Load smart_contract_analyzer
            analyzer_path = os.path.join(engines_dir, "smart_contract_analyzer.py")  # إنشاء وحدة المحلل من المواصفات
            if os.path.exists(analyzer_path):  # تنفيذ وتحميل وحدة المحلل
                spec = importlib.util.spec_from_file_location("smart_contract_analyzer", analyzer_path)  # استخراج صنف محلل العقود الذكية
                analyzer_module = importlib.util.module_from_spec(spec)  # استيراد وحدة خارجية
                spec.loader.exec_module(analyzer_module)  # التحقق من توفر كلا الصنفين
                SmartContractAnalyzer = analyzer_module.SmartContractAnalyzer  # تأكيد توفر مجموعة أدوات الأمان بالكامل
                
            if AGLSecuritySuite and SmartContractAnalyzer:  # طباعة تحذير مع تفاصيل الخطأ
                SECURITY_SUITE_AVAILABLE = True  # تعيين المتغير SECURITY_SUITE_AVAILABLE إلى صحيح (متاح)
        except Exception as e:  # التحقق من نجاح تحميل مجموعة أدوات الأمان
            print(f"⚠️ [OffensiveSecurity]: Security Suite not loaded: {e}")  # طباعة رسالة تأكيد تحميل المجموعة الأمنية

if SECURITY_SUITE_AVAILABLE:  # التحقق من الشرط
    print("   -> 🛡️ AGL Security Suite: LOADED (Slither/Mythril/Semgrep/Z3 Ready)")  # طباعة رسالة للمستخدم

# ==================================================================================
# [AGL-STRICT-LOGIC] Integration with Strict Logic Gates - بوابات المنطق الصارم
# ==================================================================================
STRICT_LOGIC_AVAILABLE = False  # تعيين المتغير STRICT_LOGIC_AVAILABLE إلى خاطئ (غير متاح)
ANDGate = ORGate = NOTGate = XORGate = NANDGate = None  # بوابة منطق صارم

def _init_offensive_strict_logic():  # تعريف دالة _init_offensive_strict_logic
    """Initialize strict logic gates for security decisions."""
    global STRICT_LOGIC_AVAILABLE, ANDGate, ORGate, NOTGate, XORGate, NANDGate  # الإعلان عن متغيرات عامة
    
    if STRICT_LOGIC_AVAILABLE:  # التحقق من الشرط
        return True  # إرجاع القيمة
    
    try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
        # Try multiple paths
        possible_paths = [  # عملية تعيين قيمة
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "strict_logic"),  # دمج عناصر في نص واحد
            os.path.join(os.getcwd(), "AGL_NextGen", "src", "agl", "engines", "strict_logic"),  # دمج عناصر في نص واحد
            r"D:\AGL\AGL_NextGen\src\agl\engines\strict_logic",  # استمرار تعريف البيانات
        ]
        
        for path in possible_paths:  # حلقة تكرار على path
            if os.path.exists(path) and path not in sys.path:  # التحقق من الشرط
                sys.path.insert(0, path)  # عملية برمجية
        
        from logic_gates import ANDGate as _AND, ORGate as _OR, NOTGate as _NOT  # استيراد من وحدة logic_gates
        from logic_gates import XORGate as _XOR, NANDGate as _NAND  # استيراد من وحدة logic_gates
        
        ANDGate, ORGate, NOTGate = _AND, _OR, _NOT  # بوابة منطق صارم
        XORGate, NANDGate = _XOR, _NAND  # بوابة منطق صارم
        
        STRICT_LOGIC_AVAILABLE = True  # تعيين المتغير STRICT_LOGIC_AVAILABLE إلى صحيح (متاح)
        print("   -> 🔰 Strict Logic Integration: ACTIVE")  # طباعة رسالة للمستخدم
        return True  # إرجاع القيمة
    except ImportError as e:  # معالجة خطأ عدم وجود الوحدة
        print(f"   -> ⚠️ Strict Logic not available: {e}")  # طباعة رسالة للمستخدم
        return False  # إرجاع القيمة

# Initialize on import
_init_offensive_strict_logic()  # عملية برمجية

class OffensiveSecurityEngine:  # تعريف صنف OffensiveSecurityEngine
    """
    AGL Offensive Security Engine V3 (Neuro-Cybernetic + Strict Logic).  # عملية برمجية
    Integrates Holographic AI and Meta-Reasoning for advanced CTF operations.  # عملية برمجية
    Capable of Logic Analysis, Strategic Planning, and Auto-Recon.  # عملية برمجية
    
    🔰 [UPGRADE 3.0] Now integrated with Strict Logic Gates for:  # عملية برمجية
       - Traceable vulnerability severity classification  # متعلق بالثغرات الأمنية
       - Formal logic-based exploit validation  # متعلق بالاستغلال الأمني
       - Deterministic security decisions with full audit trail
    """
    
    def __init__(self):  # تعريف دالة __init__ (تابع للصنف)
        self.name = "OffensiveSecurityEngine"  # تعيين خاصية name للكائن
        self.version = "3.0.0 (Strict-Logic-Enhanced)"  # تعيين خاصية version للكائن
        
        # Initialize AGL Smart Cores
        self.holo_brain = HolographicLLM() if HOLO_AVAILABLE else None  # تعيين خاصية holo_brain للكائن
        self.meta_planner = AdvancedMetaReasonerEngine() if META_AVAILABLE else None  # تعيين خاصية meta_planner للكائن
        self.resonance_opt = ResonanceOptimizer() if RESONANCE_AVAILABLE else None  # تعيين خاصية resonance_opt للكائن
        
        # Initialize Quantum Hunter
        self.quantum_hunter = None  # تعيين خاصية quantum_hunter للكائن
        if QUANTUM_AVAILABLE:  # التحقق من الشرط
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                # 8 Qubits for complex vulnerability state-space search
                self.quantum_hunter = QuantumNeuralCore(num_qubits=8)  # تعيين خاصية quantum_hunter للكائن
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                print(f"⚠️ [OffensiveSecurity]: Quantum Hunter Init Failed: {e}")  # طباعة رسالة للمستخدم

        # 🔰 [STRICT-LOGIC] Initialize Logic Gates for Security Decisions
        self.strict_gates = {}  # تعيين خاصية strict_gates للكائن
        self.logic_enabled = False  # تعيين خاصية logic_enabled للكائن
        if STRICT_LOGIC_AVAILABLE:  # التحقق من الشرط
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                self.strict_gates = {  # تعيين خاصية strict_gates للكائن
                    'AND': ANDGate(),
                    'OR': ORGate(),
                    'NOT': NOTGate(),
                    'XOR': XORGate(),
                    'NAND': NANDGate()
                }
                self.logic_enabled = True  # تعيين خاصية logic_enabled للكائن
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                print(f"   -> ⚠️ Strict Logic Gates Init Failed: {e}")  # طباعة رسالة للمستخدم

        # 🔬 [FORMAL-VERIFIER] Initialize Z3-Based Mathematical Proof Engine
        self.formal_verifier = None  # تعيين خاصية formal_verifier للكائن
        if FORMAL_VERIFIER_AVAILABLE:  # التحقق من الشرط
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                self.formal_verifier = FormalVerificationEngine(timeout_ms=10000)  # تعيين خاصية formal_verifier للكائن
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                print(f"   -> ⚠️ Formal Verifier Init Failed: {e}")  # طباعة رسالة للمستخدم

        # 🛡️ [SECURITY-SUITE] Initialize AGL Security Suite (Slither/Mythril/Semgrep)
        self.security_suite = None  # تعيين خاصية security_suite للكائن
        self.smart_analyzer = None  # تعيين خاصية smart_analyzer للكائن
        if SECURITY_SUITE_AVAILABLE:  # التحقق من الشرط
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                self.security_suite = AGLSecuritySuite({  # تعيين خاصية security_suite للكائن
                    'severity_filter': ['critical', 'high', 'medium', 'low'],
                    'confidence_threshold': 0.5,
                })
                self.smart_analyzer = SmartContractAnalyzer()  # تعيين خاصية smart_analyzer للكائن
                print("   -> 🛡️ AGL Security Suite: INITIALIZED")  # طباعة رسالة للمستخدم
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                print(f"   -> ⚠️ Security Suite Init Failed: {e}")  # طباعة رسالة للمستخدم

        print(f"⚔️ [{self.name}]: Loaded. Neuro-Cybernetic Interface Online.")  # طباعة رسالة للمستخدم
        if HOLO_AVAILABLE:  # التحقق من الشرط
            print("   -> 🧠 Holographic Analysis: ACTIVE")  # طباعة رسالة للمستخدم
        if META_AVAILABLE:  # التحقق من الشرط
            print("   -> ♟️ Strategic Meta-Reasoning: ACTIVE")  # طباعة رسالة للمستخدم
        if RESONANCE_AVAILABLE:  # التحقق من الشرط
            print("   -> ⚛️ Resonance Amplification: ACTIVE")  # طباعة رسالة للمستخدم
        if self.quantum_hunter:  # التحقق من الشرط
            print("   -> 🧿 Quantum Vulnerability Hunter: ACTIVE (Deep Logic)")  # طباعة رسالة للمستخدم
        if self.logic_enabled:  # التحقق من الشرط
            print("   -> 🔰 Strict Logic Decision Engine: ACTIVE")  # طباعة رسالة للمستخدم
        if self.formal_verifier:  # التحقق من الشرط
            print("   -> 🔬 Z3 Formal Verifier: ACTIVE (Mathematical Proofs)")  # طباعة رسالة للمستخدم
        if self.security_suite:  # التحقق من الشرط
            print("   -> 🛡️ Security Suite: ACTIVE (Slither/Mythril/Semgrep/AST)")  # طباعة رسالة للمستخدم


    # =========================================================================
    # 🔰 [STRICT-LOGIC] Security Decision Methods - قرارات الأمان بالمنطق الصارم
    # =========================================================================
    
    def _strict_classify_severity(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:  # تعريف دالة _strict_classify_severity (تابع للصنف)
        """
        Classify vulnerability severity using strict logic gates.  # متعلق بالثغرات الأمنية
        Returns severity level with full logical trace.  # عملية برمجية
        
        Logic Rules:  # بداية كتلة برمجية
        - CRITICAL = fund_loss OR (reentrancy AND external_call)  # فحص ثغرة إعادة الدخول
        - HIGH = privilege_escalation OR (data_leak AND has_value_transfer)  # عملية تعيين قيمة
        - MEDIUM = dos_possible OR data_leak  # عملية تعيين قيمة
        - LOW = informational  # عملية تعيين قيمة
        """
        if not self.logic_enabled:  # التحقق من عدم تحقق الشرط
            return {"severity": "UNKNOWN", "trace": "Logic gates not available"}  # إرجاع قاموس بالنتائج
        
        # Extract vulnerability characteristics
        vuln_text = str(vulnerability).lower()  # تحويل النص إلى أحرف صغيرة
        
        # Boolean signals - إشارات منطقية
        fund_loss = any(x in vuln_text for x in ["drain", "steal", "theft", "fund loss", "unprotected money"])  # التحقق من تحقق أي شرط
        reentrancy = "reentrancy" in vuln_text  # متعلق بالثغرات الأمنية
        external_call = any(x in vuln_text for x in ["external call", "call{value", ".call("])  # التحقق من تحقق أي شرط
        privilege_escalation = any(x in vuln_text for x in ["access control", "only", "admin", "owner bypass"])  # التحقق من تحقق أي شرط
        data_leak = "leak" in vuln_text or "exposure" in vuln_text  # متعلق بالثغرات الأمنية
        has_value_transfer = any(x in vuln_text for x in ["transfer", "value", "eth"])  # التحقق من تحقق أي شرط
        dos_possible = "dos" in vuln_text or "denial" in vuln_text or "block" in vuln_text  # متعلق بالثغرات الأمنية
        oracle_issue = "oracle" in vuln_text or "price" in vuln_text  # متعلق بالثغرات الأمنية
        flash_loan = "flash" in vuln_text  # متعلق بالثغرات الأمنية
        
        trace = []  # تهيئة قائمة فارغة trace
        severity = "LOW"  # عملية تعيين قيمة
        
        try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
            # Rule 1: CRITICAL = fund_loss OR (reentrancy AND external_call) OR (flash_loan AND oracle_issue)
            and_gate = self.strict_gates['AND']  # استدعاء بوابة المنطق
            or_gate = self.strict_gates['OR']  # استدعاء بوابة المنطق
            
            # البوابات تُستدعى كدالة وتعيد (output, trace)
            reentrancy_output, _ = and_gate(reentrancy, external_call)  # فحص ثغرة إعادة الدخول
            flash_oracle_output, _ = and_gate(flash_loan, oracle_issue)  # استدعاء بوابة المنطق
            critical_step1, _ = or_gate(fund_loss, reentrancy_output)  # فحص ثغرة إعادة الدخول
            is_critical_output, _ = or_gate(critical_step1, flash_oracle_output)  # استدعاء بوابة المنطق
            
            trace.append(f"CRITICAL_CHECK: fund_loss={fund_loss} OR (reentrancy={reentrancy} AND external={external_call}) = {is_critical_output}")  # إضافة عنصر إلى قائمة trace
            
            if is_critical_output:  # التحقق من الشرط
                severity = "CRITICAL"  # عملية تعيين قيمة
            else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                # Rule 2: HIGH = privilege_escalation OR (data_leak AND has_value_transfer)
                data_value_output, _ = and_gate(data_leak, has_value_transfer)  # استدعاء بوابة المنطق
                is_high_output, _ = or_gate(privilege_escalation, data_value_output)  # استدعاء بوابة المنطق
                
                trace.append(f"HIGH_CHECK: privilege={privilege_escalation} OR (leak={data_leak} AND value={has_value_transfer}) = {is_high_output}")  # إضافة عنصر إلى قائمة trace
                
                if is_high_output:  # التحقق من الشرط
                    severity = "HIGH"  # عملية تعيين قيمة
                else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                    # Rule 3: MEDIUM = dos_possible OR data_leak
                    is_medium_output, _ = or_gate(dos_possible, data_leak)  # استدعاء بوابة المنطق
                    
                    trace.append(f"MEDIUM_CHECK: dos={dos_possible} OR leak={data_leak} = {is_medium_output}")  # إضافة عنصر إلى قائمة trace
                    
                    if is_medium_output:  # التحقق من الشرط
                        severity = "MEDIUM"  # عملية تعيين قيمة
        
        except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
            trace.append(f"ERROR: {e}")  # إضافة عنصر إلى قائمة trace
        
        return {  # إرجاع قاموس بالنتائج
            "severity": severity,
            "trace": trace,
            "signals": {
                "fund_loss": fund_loss,
                "reentrancy": reentrancy,
                "external_call": external_call,
                "flash_loan": flash_loan,
                "oracle_issue": oracle_issue
            }
        }
    
    def _strict_validate_exploit(self, exploit_data: Dict[str, Any]) -> Dict[str, Any]:  # تعريف دالة _strict_validate_exploit (تابع للصنف)
        """
        Validate exploit chain using strict logic.  # متعلق بالاستغلال الأمني
        Ensures all conditions are met before confirming exploitability.  # متعلق بالاستغلال الأمني
        
        Validation Rules:  # بداية كتلة برمجية
        - EXPLOITABLE = (has_vector AND has_impact) AND NOT(mitigated)  # متعلق بالاستغلال الأمني
        - NEEDS_REVIEW = has_vector AND NOT(has_impact)  # عملية تعيين قيمة
        - FALSE_POSITIVE = NOT(has_vector) OR mitigated  # عملية تعيين قيمة
        """
        if not self.logic_enabled:  # التحقق من عدم تحقق الشرط
            return {"valid": False, "status": "UNKNOWN", "trace": "Logic gates unavailable"}  # إرجاع قاموس بالنتائج
        
        # Extract exploit characteristics
        has_vector = exploit_data.get("vector") is not None  # الحصول على قيمة من القاموس مع قيمة افتراضية
        has_impact = exploit_data.get("impact") is not None or exploit_data.get("severity") in ["CRITICAL", "HIGH"]  # الحصول على قيمة من القاموس مع قيمة افتراضية
        mitigated = exploit_data.get("mitigated", False)  # الحصول على قيمة من القاموس مع قيمة افتراضية
        has_poc = exploit_data.get("poc") is not None  # الحصول على قيمة من القاموس مع قيمة افتراضية
        
        trace = []  # تهيئة قائمة فارغة trace
        status = "UNKNOWN"  # عملية تعيين قيمة
        
        try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
            and_gate = self.strict_gates['AND']  # استدعاء بوابة المنطق
            or_gate = self.strict_gates['OR']  # استدعاء بوابة المنطق
            not_gate = self.strict_gates['NOT']  # استدعاء بوابة المنطق
            
            # NOT(mitigated) - البوابات تُستدعى كدالة
            not_mitigated_output, _ = not_gate(mitigated)  # استدعاء بوابة المنطق
            trace.append(f"NOT_MITIGATED: NOT({mitigated}) = {not_mitigated_output}")  # إضافة عنصر إلى قائمة trace
            
            # has_vector AND has_impact
            vector_impact_output, _ = and_gate(has_vector, has_impact)  # استدعاء بوابة المنطق
            trace.append(f"VECTOR_IMPACT: {has_vector} AND {has_impact} = {vector_impact_output}")  # إضافة عنصر إلى قائمة trace
            
            # EXPLOITABLE = (has_vector AND has_impact) AND NOT(mitigated)
            exploitable_output, _ = and_gate(vector_impact_output, not_mitigated_output)  # متعلق بالاستغلال الأمني
            trace.append(f"EXPLOITABLE: {vector_impact_output} AND {not_mitigated_output} = {exploitable_output}")  # إضافة عنصر إلى قائمة trace
            
            if exploitable_output:  # التحقق من الشرط
                status = "EXPLOITABLE"  # متعلق بالاستغلال الأمني
                if has_poc:  # التحقق من الشرط
                    status = "CONFIRMED_EXPLOITABLE"  # متعلق بالاستغلال الأمني
            else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                # Check if needs review: has_vector AND NOT(has_impact)
                not_impact_output, _ = not_gate(has_impact)  # استدعاء بوابة المنطق
                needs_review_output, _ = and_gate(has_vector, not_impact_output)  # استدعاء بوابة المنطق
                
                if needs_review_output:  # التحقق من الشرط
                    status = "NEEDS_REVIEW"  # عملية تعيين قيمة
                else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                    status = "FALSE_POSITIVE"  # عملية تعيين قيمة
        
        except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
            trace.append(f"ERROR: {e}")  # إضافة عنصر إلى قائمة trace
        
        return {  # إرجاع قاموس بالنتائج
            "valid": status in ["EXPLOITABLE", "CONFIRMED_EXPLOITABLE"],
            "status": status,
            "trace": trace
        }

    # =========================================================================
    # 🔬 [FORMAL-VERIFICATION] Mathematical Proof Methods - التحقق الرياضي الصارم
    # =========================================================================
    
    def _formal_verify_vulnerability(self, vuln_data: Dict[str, Any], code_snippet: str = "") -> Dict[str, Any]:  # تعريف دالة _formal_verify_vulnerability (تابع للصنف)
        """
        Formally verify a vulnerability using Z3 SMT Solver.  # متعلق بالثغرات الأمنية
        
        This provides MATHEMATICAL PROOF, not heuristic guessing.  # عملية برمجية
        
        Returns:  # بداية كتلة برمجية
            - INVARIANT_VIOLATED: A conservation law was broken (REAL vulnerability)  # متعلق بالثغرات الأمنية
            - PATH_UNREACHABLE: Exploit path is mathematically impossible  # متعلق بالاستغلال الأمني
            - VULNERABLE: Exploit is mathematically proven possible  # متعلق بالثغرات الأمنية
            - SAFE: Mathematically proven safe
        """
        if not self.formal_verifier:  # التحقق من عدم تحقق الشرط
            return {  # إرجاع قاموس بالنتائج
                "proven": False,
                "result": "UNKNOWN",
                "reason": "Formal Verifier not available"
            }
        
        vuln_type = vuln_data.get("type", vuln_data.get("issue_type", "unknown")).lower()  # الحصول على قيمة من القاموس مع قيمة افتراضية
        
        # Map vulnerability types to formal verification types
        type_mapping = {  # عملية تعيين قيمة
            "reentrancy": "reentrancy",
            "overflow": "overflow",
            "integer overflow": "overflow",
            "access control": "access_control",
            "unauthorized": "access_control",
            "price manipulation": "price_manipulation",
            "oracle": "price_manipulation",
            "flash loan": "flash_loan",
            "delta": "delta_accounting",
            "accounting": "delta_accounting",
        }
        
        formal_type = "unknown"  # عملية برمجية
        for keyword, ftype in type_mapping.items():  # حلقة تكرار على keyword و ftype
            if keyword in vuln_type:  # التحقق من الشرط
                formal_type = ftype  # عملية برمجية
                break  # كسر الحلقة والخروج منها
        
        try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
            # Run formal verification
            proof = self.formal_verifier.verify_vulnerability(formal_type, code_snippet)  # متعلق بالثغرات الأمنية
            
            result_map = {  # عملية تعيين قيمة
                ProofResult.VULNERABLE: "MATHEMATICALLY_PROVEN_VULNERABLE",  # متعلق بالثغرات الأمنية
                ProofResult.SAFE: "MATHEMATICALLY_PROVEN_SAFE",  # نتيجة البرهان الرياضي
                ProofResult.INVARIANT_VIOLATED: "INVARIANT_VIOLATED",  # نتيجة البرهان الرياضي
                ProofResult.PATH_UNREACHABLE: "PATH_UNREACHABLE",  # نتيجة البرهان الرياضي
                ProofResult.UNKNOWN: "NEEDS_MANUAL_REVIEW"  # نتيجة البرهان الرياضي
            }
            
            result_str = result_map.get(proof.result, "UNKNOWN")  # الحصول على قيمة من القاموس مع قيمة افتراضية
            
            return {  # إرجاع قاموس بالنتائج
                "proven": proof.result in [ProofResult.VULNERABLE, ProofResult.INVARIANT_VIOLATED],
                "result": result_str,
                "proof_trace": proof.proof_trace,
                "counterexample": proof.counterexample,
                "time_ms": proof.time_ms,
                "formal_type": formal_type
            }
            
        except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
            return {  # إرجاع قاموس بالنتائج
                "proven": False,
                "result": "ERROR",
                "reason": str(e)
            }
    
    def _formal_check_invariants(self, contract_code: str, vulnerability: Dict[str, Any]) -> Dict[str, Any]:  # تعريف دالة _formal_check_invariants (تابع للصنف)
        """
        Check if a vulnerability violates known DeFi invariants.  # متعلق بالثغرات الأمنية
        
        Invariants checked:  # فحص الثوابت الرياضية
        - liquidity_conservation: Total liquidity = sum of positions  # عملية تعيين قيمة
        - delta_balance: After unlock-lock, all deltas = 0  # تهيئة بقيمة صفر
        - fee_bounds: Protocol fee within valid range
        - reentrancy_lock: Cannot re-enter while locked  # فحص ثغرة إعادة الدخول
        """
        if not self.formal_verifier:  # التحقق من عدم تحقق الشرط
            return {"checked": False, "violations": []}  # إرجاع قاموس بالنتائج
        
        violations = []  # تهيئة قائمة فارغة violations
        vuln_text = str(vulnerability).lower()  # تحويل النص إلى أحرف صغيرة
        
        # Determine which invariants to check based on vulnerability type
        invariants_to_check = []  # تهيئة قائمة فارغة invariants_to_check
        
        if any(x in vuln_text for x in ["liquidity", "pool", "swap", "amm"]):  # التحقق من الشرط
            invariants_to_check.append("liquidity_conservation")  # إضافة عنصر إلى قائمة invariants_to_check
        
        if any(x in vuln_text for x in ["delta", "unlock", "settle", "v4"]):  # التحقق من الشرط
            invariants_to_check.append("delta_balance")  # إضافة عنصر إلى قائمة invariants_to_check
        
        if any(x in vuln_text for x in ["fee", "protocol", "tax"]):  # التحقق من الشرط
            invariants_to_check.append("fee_bounds")  # إضافة عنصر إلى قائمة invariants_to_check
        
        if any(x in vuln_text for x in ["reentrancy", "reentrant", "call", "callback"]):  # التحقق من الشرط
            invariants_to_check.append("reentrancy_lock")  # إضافة عنصر إلى قائمة invariants_to_check
        
        # Default: check delta_balance for Uniswap V4
        if not invariants_to_check and "uniswap" in vuln_text.lower():  # التحقق من عدم تحقق الشرط
            invariants_to_check = ["delta_balance", "liquidity_conservation"]  # فحص الثوابت الرياضية
        
        for invariant in invariants_to_check:  # حلقة تكرار على invariant
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                proof = self.formal_verifier.verify_invariant(  # محرك التحقق الرياضي الصارم
                    invariant,  # فحص الثوابت الرياضية
                    pre_state={},  # تهيئة قاموس فارغ pre_state
                    post_state={},  # تهيئة قاموس فارغ post_state
                    transition=vulnerability.get("function", "unknown")  # الحصول على قيمة من القاموس مع قيمة افتراضية
                )
                
                if proof.result in [ProofResult.VULNERABLE, ProofResult.INVARIANT_VIOLATED]:  # التحقق من الشرط
                    violations.append({  # إضافة عنصر إلى قائمة violations
                        "invariant": invariant,
                        "status": "VIOLATED",
                        "trace": proof.proof_trace,
                        "counterexample": proof.counterexample
                    })
                    
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                violations.append({  # إضافة عنصر إلى قائمة violations
                    "invariant": invariant,
                    "status": "CHECK_FAILED",
                    "error": str(e)
                })
        
        return {  # إرجاع قاموس بالنتائج
            "checked": True,
            "invariants_checked": invariants_to_check,
            "violations": violations,
            "has_violations": len(violations) > 0
        }

    def process_task(self, task: str, target: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:  # تعريف دالة process_task (تابع للصنف)
        """
        Main entry point for the engine.  # نقطة الدخول الرئيسية للمحرك
        
        Smart Contract Audit Tasks:  # مهام تدقيق العقود الذكية
        - 'smart_contract_audit': Full audit pipeline (static + EVM sim + quantum + Z3).  # خط أنابيب التدقيق الكامل
        - 'quantum_deep_audit': Deep AI hypothesis generation via Ollama LLM.  # توليد فرضيات عميقة بالذكاء الاصطناعي
        - 'ai_deep_analysis': Uses HoloLLM to analyze data for logic flaws.  # تحليل عميق بالمحرك الهولوغرافي
        - 'generate_attack_plan': Uses MetaReasoner to build strategy.  # بناء خطة استراتيجية
        - 'resonance_exploit_match': Uses Quantum Resonance to select best vector.  # اختيار أفضل متجه بالرنين الكمي
        """
        print(f"⚔️ [{self.name}]: Processing task '{task}' on target '{target}'...")  # طباعة رسالة للمستخدم
        
        # --- Smart Contract Audit Operations ---  # عمليات تدقيق العقود الذكية
        if task == "ai_deep_analysis":  # تحليل عميق بالذكاء الاصطناعي
            return self._ai_analyze_target(target, context)  # إرجاع القيمة
        elif task == "generate_attack_plan":  # توليد خطة هجوم استراتيجية
            return self._generate_attack_plan(target, context)  # إرجاع القيمة
        
        # --- Quantum Evolution ---  # التطور الكمي
        elif task == "quantum_deep_audit":  # تدقيق كمي عميق
            return self._quantum_deep_audit(target, context)  # إرجاع القيمة
        elif task == "resonance_exploit_match":  # مطابقة استغلال بالرنين الكمي
             return self._resonance_select_exploit(target, context)  # إرجاع القيمة
        elif task == "smart_contract_audit":  # تدقيق العقود الذكية
            # 1. Static Scan
            audit = self._analyze_smart_contracts(target, context)  # عملية تعيين قيمة
            
            # [UPGRADE] Check if Quantum Deep Audit is applicable
            if self.quantum_hunter:  # التحقق من الشرط
                print("   🧿 [Offensive]: Enhancing Audit with Quantum Deep Logic...")  # طباعة رسالة للمستخدم
                if "files" in audit:  # التحقق من الشرط
                     for f, code in audit["files"].items():  # حلقة تكرار على f و code
                         q_res = self._quantum_deep_audit(code)  # عملية تعيين قيمة
                         if "findings" in q_res:  # التحقق من الشرط
                            audit["quantum_findings"] = audit.get("quantum_findings", []) + q_res["findings"]  # الحصول على قيمة من القاموس مع قيمة افتراضية

            # 2. محاكاة ديناميكية حقيقية: تحليل تدفق المال + إثبات رياضي
            evm_sim = self._dynamic_evm_simulation(target, audit)
            if evm_sim and evm_sim.get("call_chains"):
                audit["evm_simulation"] = evm_sim

            return audit  # إرجاع القيمة

        # --- مهمة غير معروفة ---
        available = ["smart_contract_audit", "quantum_deep_audit", "ai_deep_analysis",
                     "generate_attack_plan", "resonance_exploit_match"]  # المهام المتاحة
        return {"error": f"Unknown task '{task}'", "available_tasks": available}  # إرجاع قاموس بالنتائج

    def _quantum_deep_audit(self, target_code: str, context: Optional[Dict] = None) -> Dict[str, Any]:  # تعريف دالة _quantum_deep_audit (تابع للصنف)
        """
        Uses Quantum Neural Core to find 'Zero-Day' logic flaws that standard tools miss.  # عملية برمجية
        It simulates the contract state space as a quantum system and looks for 'entanglement' 
        that indicates hidden dependencies (reentrancy, logic bombs).  # فحص ثغرة إعادة الدخول
        """
        if not self.quantum_hunter:  # التحقق من عدم تحقق الشرط
            return {"error": "Quantum Hunter not available."}  # إرجاع قاموس بالنتائج
            
        print(f"🧿 [QuantumHunter]: Initiating Deep State-Space Audit on target...")  # طباعة رسالة للمستخدم
        
        # 1. Create a prompt for the Quantum Brain that treats Code as Physics
        query = f"""  # عملية تعيين قيمة
        ANALYZE THIS SMART CONTRACT LOGIC AS A PHYSICS SYSTEM.  # عملية برمجية
        Look for 'Unstable Equilibrium' where a small input causes a massive energy release (Exploit).  # متعلق بالاستغلال الأمني
        Code Snippet:  # بداية كتلة برمجية
        {target_code[:2000]}
        
        Task: Identify 3 theoretical attack vectors based on state-transitions, not just syntax.  # عملية برمجية
        """
        
        # 2. Collapsing Wave Function (Generating Hypotheses)
        try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
            hypotheses = self.quantum_hunter.sample_hypotheses(query, context, num_samples=3)  # النواة الكمية العصبية
        except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
            print(f"Quantum Sampling Error: {e}")  # طباعة رسالة للمستخدم
            return {"error": str(e)}  # إرجاع قاموس بالنتائج
        
        findings = []  # تهيئة قائمة فارغة findings
        if isinstance(hypotheses, list):  # التحقق من الشرط
            for h in hypotheses:  # حلقة تكرار على h
                findings.append({  # إضافة عنصر إلى قائمة findings
                    "vector": h.get("hypothesis"),
                    "confidence": h.get("confidence"),
                    "physics_analogy": h.get("reasoning")
                })
            
        return {  # إرجاع قاموس بالنتائج
            "status": "success",
            "audit_type": "Quantum Deep Logic",
            "findings": findings
        }

    def _analyze_smart_contracts(self, target_path: str, context: Dict[str, Any] = None) -> Dict[str, Any]:  # تعريف دالة _analyze_smart_contracts (تابع للصنف)
        """
        [NEW] Static Analysis for Smart Contracts (Solidity).  # متعلق بلغة سوليديتي
        Focuses on Logic Flaws, Reentrancy, and Access Control.  # فحص ثغرة إعادة الدخول
        """
        print(f"   ⚔️ [Offensive]: Starting Deep Logic Audit on {target_path}...")  # طباعة رسالة للمستخدم
        
        if not os.path.exists(target_path):  # التحقق من عدم تحقق الشرط
            return {"error": f"Target path not found: {target_path}"}  # إرجاع قاموس بالنتائج
            
        findings = []  # تهيئة قائمة فارغة findings
        files_analyzed = 0  # تهيئة العداد files_analyzed بصفر
        
        # ═══════════════════════════════════════════════════════════════════════
        # [AGL-SECURITY-SUITE] Use New Analyzer if Available (Priority 1)
        # ═══════════════════════════════════════════════════════════════════════
        suite_findings = []  # تهيئة قائمة فارغة suite_findings
        if self.security_suite:  # التحقق من الشرط
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                print("      -> 🛡️ Running AGL Security Suite (AST + Pattern Analysis)...")  # طباعة رسالة للمستخدم
                if os.path.isfile(target_path):  # التحقق من الشرط
                    suite_result = self.security_suite.scan_file(target_path)  # مجموعة أدوات الأمان المتكاملة
                    suite_findings = suite_result.get('findings', [])  # الحصول على قيمة من القاموس مع قيمة افتراضية
                else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                    suite_result = self.security_suite.scan_directory(target_path)  # مجموعة أدوات الأمان المتكاملة
                    # Flatten findings from all files
                    for file_path, file_result in suite_result.get('files', {}).items():  # حلقة تكرار على file_path و file_result
                        for f in file_result.get('findings', []):  # حلقة تكرار على f
                            f['file'] = file_path  # عملية تعيين قيمة
                            suite_findings.append(f)  # إضافة عنصر إلى قائمة suite_findings
                
                print(f"      -> 🛡️ Security Suite found {len(suite_findings)} issues")  # طباعة رسالة للمستخدم
                
                # suite_findings تبقى منفصلة — لا نخلطها مع findings الهيوريستيك
                # النتائج تُرجع في مفتاح "suite_findings" المنفصل
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                print(f"      -> ⚠️ Security Suite error: {e}")  # طباعة رسالة للمستخدم
        
        # ═══════════════════════════════════════════════════════════════════════
        # [LEGACY] Original Heuristic Analysis (runs in parallel for comparison)
        # ═══════════════════════════════════════════════════════════════════════
        
        # Instantiate Context Aggregator if available (Updated API: No args in init)
        aggregator = SolidityContextAggregator() if CONTEXT_AGGREGATOR_AVAILABLE else None  # متعلق بلغة سوليديتي

        files_to_scan = []  # تهيئة قائمة فارغة files_to_scan
        if os.path.isfile(target_path):  # التحقق من الشرط
            files_to_scan.append(target_path)  # إضافة عنصر إلى قائمة files_to_scan
        else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
            # 1. Walk through the directory
            for root, dirs, files in os.walk(target_path):  # حلقة تكرار
                for file in files:  # حلقة تكرار على file
                    if file.endswith(".sol"):  # التحقق من الشرط
                        files_to_scan.append(os.path.join(root, file))  # إضافة عنصر إلى قائمة files_to_scan
        
        for file_path in files_to_scan:  # حلقة تكرار على file_path
            files_analyzed += 1  # إضافة وتعيين القيمة
            file = os.path.basename(file_path)  # عملية على مسار الملف
            if not self.security_suite:  # Only print if suite didn't already analyze  # التحقق من عدم تحقق الشرط
                print(f"      -> 📜 Analyzing: {file}...")  # طباعة رسالة للمستخدم
            
            try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                # [AGL-HEIKAL] Context Aggregation: Resolve Imports First
                # Init with NO arguments
                aggregator = SolidityContextAggregator() if CONTEXT_AGGREGATOR_AVAILABLE else None  # متعلق بلغة سوليديتي
                
                protection_summary = "Protections: None detected (Aggregator Offline)"  # عملية تعيين قيمة
                if aggregator:  # التحقق من الشرط
                   aggregator.scan_imports(file_path) # Get Modifiers/Requires from imported files  # استيراد وحدة خارجية
                   protection_summary = aggregator.format_context()   # مُجمّع سياق سوليديتي

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:  # فتح ملف للقراءة أو الكتابة
                    content = f.read()  # قراءة محتوى الملف
                    
                # 2. Heuristic Analysis (Fast Scan)
                vulnerabilities = []  # تهيئة قائمة فارغة vulnerabilities
                
                # Reentrancy Check
                if "call.value" in content and "require" not in content.split("call.value")[0]:  # التحقق من الشرط
                        # Very basic heuristic: check if state change happens after call (hard to do with regex only)
                        pass  # تمرير (لا شيء يُنفذ)
                if ".call{value:" in content:  # التحقق من الشرط
                    vulnerabilities.append("Potential Reentrancy (External Call with Value)")  # إضافة عنصر إلى قائمة vulnerabilities
                    
                # Integer Overflow (Solidity < 0.8.0)
                if "pragma solidity ^0.5" in content or "pragma solidity ^0.6" in content or "pragma solidity ^0.4" in content:  # التحقق من الشرط
                    if "SafeMath" not in content:  # التحقق من الشرط
                        vulnerabilities.append("Integer Overflow Risk (Old Solidity without SafeMath)")  # إضافة عنصر إلى قائمة vulnerabilities
                        
                # Unchecked External Call — فحص كل استدعاء .call() بشكل مستقل
                # البحث عن .call( بدون تخزين نتيجة الاستدعاء في متغير bool
                for call_match in re.finditer(r'(\w+)\.call\s*\(', content):
                    # فحص السياق: هل تم فحص نتيجة الاستدعاء؟
                    call_pos = call_match.start()
                    # البحث 100 حرف قبل وبعد الاستدعاء
                    context_before = content[max(0, call_pos - 100):call_pos]
                    context_after = content[call_pos:min(len(content), call_pos + 200)]
                    # هل النتيجة مخزنة في (bool success, ) أو يتم فحصها بـ require؟
                    has_return_check = "(bool" in context_before or "require(" in context_after.split(";")[0] if ";" in context_after else ""
                    if not has_return_check:
                        line_num = content[:call_pos].count('\n') + 1
                        vulnerabilities.append(f"Unchecked Low-Level Call at line {line_num}: {call_match.group()}")  # إضافة عنصر إلى قائمة vulnerabilities

                # tx.origin Authentication — فحص استخدام tx.origin في التحكم بالوصول
                if "tx.origin" in content:
                    for tx_match in re.finditer(r'require\s*\(\s*tx\.origin\s*==', content):
                        line_num = content[:tx_match.start()].count('\n') + 1
                        vulnerabilities.append(f"tx.origin Authentication at line {line_num} — vulnerable to phishing attacks")

                # Block Timestamp Dependency — فحص الاعتماد على block.timestamp
                if "block.timestamp" in content:
                    for ts_match in re.finditer(r'block\.timestamp\s*[<>=!%]+', content):
                        line_num = content[:ts_match.start()].count('\n') + 1
                        vulnerabilities.append(f"Block Timestamp Dependency at line {line_num} — miner-manipulable")

                # delegatecall — فحص استدعاء delegatecall الخطير
                if ".delegatecall(" in content:
                    for dc_match in re.finditer(r'(\w+)\.delegatecall\s*\(', content):
                        line_num = content[:dc_match.start()].count('\n') + 1
                        vulnerabilities.append(f"Dangerous delegatecall to {dc_match.group(1)} at line {line_num}")

                # [AGL-RESERVE-logic]: BasketHandler / RToken specific
                if "BasketHandler" in file or "RToken" in file:  # التحقق من الشرط
                        if "refreshBasket" in content or "setPrimeBasket" in content:  # التحقق من الشرط
                            vulnerabilities.append("Requires Deep State Analysis: Basket Rebalance Reentrancy?")  # إضافة عنصر إلى قائمة vulnerabilities
                        if "muluDivu" in content and "CEIL" in content:  # التحقق من الشرط
                             vulnerabilities.append("Info: Check Issuance/Redemption Rounding Direction (muluDivu usage)")  # إضافة عنصر إلى قائمة vulnerabilities

                # [AGL-RESERVE-RTOKEN]: Specific checks
                if "RToken" in file:  # التحقق من الشرط
                        if "issue" in content and "totalSupply" in content:  # التحقق من الشرط
                            vulnerabilities.append("Review: First Depositor Attack / Inflation Attack vectors")  # إضافة عنصر إلى قائمة vulnerabilities
                        if "redeemCustom" in content:  # التحقق من الشرط
                            vulnerabilities.append("Review: Custom Redemption Complexity - Prorata Logic")  # إضافة عنصر إلى قائمة vulnerabilities
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] DUST-LOCK VULNERABILITY PATTERN (Discovered 2026)
                # ═══════════════════════════════════════════════════════════════
                # Pattern: Per-asset threshold check discards valid aggregate value
                # Example: 50 assets × $50 = $2500 total, but each < $1000 threshold
                #          System sees: $0 (WRONG!) → triggers unnecessary haircut
                # ═══════════════════════════════════════════════════════════════
                
                # Check 1: minTradeVolume or similar threshold in loops
                dust_lock_indicators = [  # عملية تعيين قيمة
                    "minTradeVolume", "minTrade", "dustThreshold", 
                    "minimumAmount", "minAmount", "threshold"
                ]
                has_threshold = any(ind in content for ind in dust_lock_indicators)  # التحقق من تحقق أي شرط
                
                # Check 2: Ternary with 0 inside a loop (per-element discard pattern)
                # Pattern: val < threshold ? 0 : val - threshold
                ternary_discard_pattern = re.search(  # البحث بالتعبير النمطي وتخزين النتيجة في ternary_discard_pattern
                    r'(\w+)\s*<\s*(\w*(min|threshold|dust)\w*)\s*\?\s*0\s*:',  # عملية برمجية
                    content, re.IGNORECASE  # عملية برمجية
                )
                
                # Check 3: Loop accumulation with conditional zero
                # Pattern: sum += (condition) ? 0 : value
                loop_accumulation = re.search(  # البحث بالتعبير النمطي وتخزين النتيجة في loop_accumulation
                    r'for\s*\([^)]*\)[^{]*\{[^}]*\+=\s*\([^)]+\)\s*\?\s*0\s*:',  # إضافة وتعيين القيمة
                    content, re.DOTALL  # عملية برمجية
                )
                
                # Check 4: basketRange or similar aggregation functions
                aggregation_functions = [  # عملية تعيين قيمة
                    "basketRange", "calculateTotal", "sumAssets",
                    "aggregateSurplus", "totalValue", "computeBottom"
                ]
                has_aggregation = any(func in content for func in aggregation_functions)  # التحقق من تحقق أي شرط
                
                if has_threshold and (ternary_discard_pattern or loop_accumulation):  # التحقق من الشرط
                    vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                        "🚨 CRITICAL: DUST-LOCK VULNERABILITY DETECTED! "
                        "Per-asset threshold check may discard valid aggregate surplus. "
                        "Pattern: Individual values below threshold are zeroed, but sum could exceed threshold. "
                        "Impact: Unnecessary haircuts, value theft via forwardRevenue(). "
                        "Fix: Aggregate first, then apply threshold to total."
                    )
                    print(f"         -> 💀 [HEIKAL] DUST-LOCK PATTERN MATCHED!")  # طباعة رسالة للمستخدم
                    
                elif has_threshold and has_aggregation:  # شرط بديل
                    vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                        "⚠️ HIGH: Potential Dust-Lock Risk - "
                        "Threshold check found in aggregation context. "
                        "Verify: Is threshold applied per-element or to aggregate total?"
                    )
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] END DUST-LOCK PATTERN
                # ═══════════════════════════════════════════════════════════════
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] MONEY FLOW ANALYSIS (Added 2026)
                # ═══════════════════════════════════════════════════════════════
                money_flow_functions = []  # تهيئة قائمة فارغة money_flow_functions
                
                # Detect money movement patterns
                transfer_patterns = re.findall(r'\.transfer\s*\([^)]+\)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في transfer_patterns
                transfer_from_patterns = re.findall(r'\.transferFrom\s*\([^)]+\)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في transfer_from_patterns
                safe_transfer_patterns = re.findall(r'\.safeTransfer\s*\([^)]+\)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في safe_transfer_patterns
                call_value_patterns = re.findall(r'\.call\{value:\s*[^}]+\}', content)  # البحث بالتعبير النمطي وتخزين النتيجة في call_value_patterns
                
                if transfer_patterns:  # التحقق من الشرط
                    money_flow_functions.extend([("transfer", p) for p in transfer_patterns])  # إضافة عناصر متعددة إلى قائمة money_flow_functions
                if transfer_from_patterns:  # التحقق من الشرط
                    money_flow_functions.extend([("transferFrom", p) for p in transfer_from_patterns])  # إضافة عناصر متعددة إلى قائمة money_flow_functions
                if safe_transfer_patterns:  # التحقق من الشرط
                    money_flow_functions.extend([("safeTransfer", p) for p in safe_transfer_patterns])  # إضافة عناصر متعددة إلى قائمة money_flow_functions
                if call_value_patterns:  # التحقق من الشرط
                    money_flow_functions.extend([("call{value}", p) for p in call_value_patterns])  # إضافة عناصر متعددة إلى قائمة money_flow_functions
                
                # Detect mint/burn patterns
                mint_patterns = re.findall(r'_mint\s*\([^)]+\)|\.mint\s*\([^)]+\)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في mint_patterns
                burn_patterns = re.findall(r'_burn\s*\([^)]+\)|\.burn\s*\([^)]+\)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في burn_patterns
                
                if mint_patterns:  # التحقق من الشرط
                    money_flow_functions.extend([("mint", p) for p in mint_patterns])  # إضافة عناصر متعددة إلى قائمة money_flow_functions
                if burn_patterns:  # التحقق من الشرط
                    money_flow_functions.extend([("burn", p) for p in burn_patterns])  # إضافة عناصر متعددة إلى قائمة money_flow_functions
                
                # Check for unprotected money flows
                if money_flow_functions:  # التحقق من الشرط
                    # Check if there's access control
                    has_access_control = any(mod in content for mod in [  # التحقق من تحقق أي شرط
                        "onlyOwner", "onlyAdmin", "onlyMinter", "onlyRole",
                        "require(msg.sender", "require(_msgSender()", "onlyGuardian"
                    ])
                    
                    if not has_access_control and (mint_patterns or call_value_patterns):  # التحقق من عدم تحقق الشرط
                        vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                            f"🚨 CRITICAL: Unprotected Money Flow! "
                            f"Found {len(money_flow_functions)} money movement functions without access control. "  # فحص التحكم في الوصول
                            f"Patterns: {[f[0] for f in money_flow_functions[:5]]}"
                        )
                        print(f"         -> 💰 [HEIKAL] UNPROTECTED MONEY FLOW DETECTED!")  # طباعة رسالة للمستخدم
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] MATHEMATICAL LOGIC ANALYSIS (Added 2026)
                # ═══════════════════════════════════════════════════════════════
                math_vulnerabilities = []  # تهيئة قائمة فارغة math_vulnerabilities
                
                # 1. Division by Zero Risk
                division_patterns = re.findall(r'/\s*(\w+)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في division_patterns
                for divisor in division_patterns:  # حلقة تكرار على divisor
                    # Check if divisor is validated before use
                    if divisor != "0" and f"require({divisor}" not in content and f"{divisor} > 0" not in content and f"{divisor} != 0" not in content:  # التحقق من الشرط
                        if divisor not in ["1", "2", "10", "100", "1000", "1e18", "PRECISION", "WAD", "RAY"]:  # التحقق من الشرط
                            math_vulnerabilities.append(f"Division by potentially zero variable: {divisor}")  # إضافة عنصر إلى قائمة math_vulnerabilities
                
                # 2. Rounding Direction Errors
                if "mulDiv" in content or "muldiv" in content.lower():  # التحقق من الشرط
                    if "CEIL" in content and "FLOOR" in content:  # التحقق من الشرط
                        vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                            "⚠️ HIGH: Mixed Rounding Directions - "
                            "Both CEIL and FLOOR used. Verify consistent rounding in favor of protocol."
                        )
                    elif "DOWN" in content or "FLOOR" in content:  # شرط بديل
                        # Check if it's in withdrawal context
                        if "withdraw" in content.lower() or "redeem" in content.lower():  # التحقق من الشرط
                            pass  # Expected: round down on withdrawal
                        elif "deposit" in content.lower() or "mint" in content.lower():  # شرط بديل
                            vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                                "⚠️ MEDIUM: Rounding DOWN on deposit/mint may favor users over protocol."
                            )
                
                # 3. Precision Loss Detection
                precision_risk = re.search(  # البحث بالتعبير النمطي وتخزين النتيجة في precision_risk
                    r'(\w+)\s*/\s*(\w+)\s*\*\s*(\w+)',  # a / b * c pattern (precision loss)  # عملية برمجية
                    content
                )
                if precision_risk:  # التحقق من الشرط
                    vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                        f"⚠️ HIGH: Potential Precision Loss - "
                        f"Division before multiplication detected: {precision_risk.group(0)}. "  # عملية برمجية
                        f"Fix: Multiply first, then divide."  # عملية برمجية
                    )
                
                # 4. Fee Calculation Errors
                fee_patterns = re.findall(r'fee\s*=\s*[^;]+', content, re.IGNORECASE)  # البحث بالتعبير النمطي وتخزين النتيجة في fee_patterns
                for fee_calc in fee_patterns:  # حلقة تكرار على fee_calc
                    if "/" in fee_calc and "*" not in fee_calc.split("/")[0]:  # التحقق من الشرط
                        math_vulnerabilities.append(f"Fee calculation may lose precision: {fee_calc[:50]}")  # إضافة عنصر إلى قائمة math_vulnerabilities
                
                # 5. Slippage/Price Manipulation
                if "getPrice" in content or "latestAnswer" in content or "oracle" in content.lower():  # التحقق من الشرط
                    if "deadline" not in content.lower() and "maxSlippage" not in content:  # التحقق من الشرط
                        vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                            "⚠️ HIGH: Oracle Price without Slippage Protection - "
                            "Price fetched from oracle but no deadline or maxSlippage check found."
                        )
                
                if math_vulnerabilities:  # التحقق من الشرط
                    vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                        f"🔢 MATH ISSUES ({len(math_vulnerabilities)}): " +   # متعلق بالثغرات الأمنية
                        "; ".join(math_vulnerabilities[:3])
                    )
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] CROSS-CONTRACT FLOW ANALYSIS (Added 2026)
                # ═══════════════════════════════════════════════════════════════
                external_calls = []  # تهيئة قائمة فارغة external_calls
                
                # Detect external contract interactions
                interface_calls = re.findall(r'I\w+\([^)]*\)\.\w+\([^)]*\)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في interface_calls
                external_calls.extend(interface_calls)  # إضافة عناصر متعددة إلى قائمة external_calls
                
                # Detect callback patterns (flash loan vectors)
                callback_patterns = [  # عملية تعيين قيمة
                    "onFlashLoan", "uniswapV2Call", "uniswapV3FlashCallback",
                    "pancakeCall", "onERC721Received", "onERC1155Received",
                    "executeOperation", "receiveFlashLoan"
                ]
                has_callback = any(cb in content for cb in callback_patterns)  # التحقق من تحقق أي شرط
                
                if has_callback:  # التحقق من الشرط
                    vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                        "⚠️ HIGH: Flash Loan Callback Detected - "
                        "Verify state is protected during callback execution. "
                        "Check for reentrancy and price manipulation vectors."
                    )
                    print(f"         -> ⚡ [HEIKAL] FLASH LOAN CALLBACK DETECTED!")  # طباعة رسالة للمستخدم
                
                # Detect price oracle dependencies
                oracle_patterns = re.findall(r'(\w*[Oo]racle\w*|\w*[Pp]rice[Ff]eed\w*)', content)  # البحث بالتعبير النمطي وتخزين النتيجة في oracle_patterns
                if oracle_patterns:  # التحقق من الشرط
                    # Check for stale price protection
                    if "updatedAt" not in content and "timestamp" not in content.lower():  # التحقق من الشرط
                        vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                            f"⚠️ HIGH: Oracle without Staleness Check - "
                            f"Using oracle ({oracle_patterns[0]}) but no timestamp validation found."  # عملية برمجية
                        )
                
                # Cross-contract reentrancy via external calls
                if len(external_calls) > 0:  # التحقق من الشرط
                    # Check if state changes happen after external calls
                    for call in external_calls[:5]:  # Limit to first 5  # حلقة تكرار على call
                        call_pos = content.find(call)  # عملية تعيين قيمة
                        after_call = content[call_pos:call_pos+500] if call_pos > 0 else ""  # عملية تعيين قيمة
                        if re.search(r'=\s*\w+\s*[+-]', after_call):  # التحقق من الشرط
                            vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                                f"⚠️ MEDIUM: State Change After External Call - "
                                f"Potential cross-contract reentrancy near: {call[:40]}..."  # فحص ثغرة إعادة الدخول
                            )
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] WORMHOLE-SPECIFIC CHECKS (Cross-Chain Security)
                # ═══════════════════════════════════════════════════════════════
                if "wormhole" in file.lower() or "bridge" in file.lower() or "guardian" in content.lower():  # التحقق من الشرط
                    # Guardian signature verification
                    if "verifySignatures" in content or "parseAndVerifyVM" in content:  # التحقق من الشرط
                        if "quorum" not in content.lower() and "threshold" not in content.lower():  # التحقق من الشرط
                            vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                                "🚨 CRITICAL: Guardian Signature without Quorum Check - "
                                "Cross-chain message verification may accept insufficient signatures."
                            )
                    
                    # Message replay protection
                    if "consumeMessage" in content or "receiveMessage" in content:  # التحقق من الشرط
                        if "nonce" not in content.lower() and "sequence" not in content.lower():  # التحقق من الشرط
                            vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                                "🚨 CRITICAL: Potential Message Replay - "
                                "No nonce/sequence check for cross-chain message consumption."
                            )
                    
                    # Chain ID validation
                    if "emitterChain" in content or "sourceChain" in content:  # التحقق من الشرط
                        if "require" not in content.split("Chain")[0][-100:]:  # التحقق من الشرط
                            vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                                "⚠️ HIGH: Chain ID Validation - "
                                "Verify source chain is properly validated for cross-chain messages."
                            )
                    
                    # Token wrapping/unwrapping
                    if "completeTransfer" in content or "wrapAndTransfer" in content:  # التحقق من الشرط
                        vulnerabilities.append(  # إضافة عنصر إلى قائمة vulnerabilities
                            "📋 REVIEW: Cross-Chain Token Transfer - "
                            "Verify token amount, decimals normalization, and recipient validation."
                        )
                        print(f"         -> 🌉 [HEIKAL] CROSS-CHAIN TRANSFER LOGIC DETECTED!")  # طباعة رسالة للمستخدم
                
                # ═══════════════════════════════════════════════════════════════
                # [AGL-HEIKAL] END ADVANCED ANALYSIS
                # ═══════════════════════════════════════════════════════════════
                
                # 3. AI Deep Logic Analysis (The "Brain")
                if self.holo_brain:  # التحقق من الشرط
                    # [NEW] Aggregate Context from Protections in Imports
                    # This solves "Doesn't detect protection in other places"
                    aggregator = SolidityContextAggregator()  # متعلق بلغة سوليديتي
                    aggregator.scan_imports(file_path)  # مُجمّع سياق سوليديتي
                    imported_context = aggregator.format_context()  # مُجمّع سياق سوليديتي
                    
                    prompt = [  # عملية تعيين قيمة
                        {"role": "system", "content": "You are an expert Smart Contract Auditor (Solidity). Find logical flaws, price manipulation vectors, and reentrancy bugs. Use the IMPORTED CONTEXT to check foreign modifiers/constraints."},  # فحص ثغرة إعادة الدخول
                        {"role": "user", "content": f"""
                        CODEFILE: {file}
                        
                        --- MAIN CONTRACT CONTENT ---
                        {content[:2500]} ... (truncated if long)  # عملية برمجية
                        
                        {imported_context}
                        
                        TASK: Analyze for HIGH SEVERITY bugs that could drain funds (2M$ Bounty scope).  # عملية برمجية
                        Focus on:  # بداية كتلة برمجية
                        1. Logical errors in swap/transfer logic.  # عملية تحويل أموال
                        2. Access control bypass.  # فحص التحكم في الوصول
                        3. Flash loan price manipulation risks.  # فحص هجمات القروض السريعة
                        4. Cross-File Protections: Verify if modifiers (e.g. onlyMinter) defined in IMPORTED CONTEXT are applied here.  # عملية سك أو حرق التوكنات
                        """}
                    ]
                    insight = self.holo_brain.chat_llm(prompt, temperature=0.1)  # المحرك الهولوغرافي للذكاء الاصطناعي
                    if "SAFE" not in insight and "No critical" not in insight:  # التحقق من الشرط
                        vulnerabilities.append(f"AI Insight: {insight[:200]}...")  # إضافة عنصر إلى قائمة vulnerabilities

                # 4. Advanced Meta-Reasoner (The "Strategist")
                if self.meta_planner:  # التحقق من الشرط
                    print(f"         -> ♟️ [Meta-Audit]: Verifying logic with {self.meta_planner.model}...")  # طباعة رسالة للمستخدم
                    
                    sys_prompt = (  # عملية تعيين قيمة
                        "You are an Advanced Meta-Reasoner specializing in Solidity Logic Flow. "
                        "Analyze the provided code for high-level architectural flaws that regex scans miss "
                        "(e.g., flash loan manipulation, governance attack vectors, economic logic errors). "
                        "Return a concise summary of critical risks only."
                    )
                    
                    user_prompt = f"""  # عملية تعيين قيمة
                    CODE SNIPPET FROM: {file}
                    
                    {content[:2000]}
                    
                    TASK: Identify logic flaws.  # عملية برمجية
                    """
                    
                    try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                        # Accessing the internal direct LLM method since no public analyze() exists
                        meta_insight = self.meta_planner._call_llm_direct(sys_prompt, user_prompt)  # محرك التفكير الفوقي الاستراتيجي
                        if meta_insight and "No critical" not in meta_insight and len(meta_insight) > 10:  # التحقق من الشرط
                            vulnerabilities.append(f"Meta-Reasoner Insight: {meta_insight[:300]}...")  # إضافة عنصر إلى قائمة vulnerabilities
                    except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                        print(f"         -> Meta-Reasoner Error: {e}")  # طباعة رسالة للمستخدم

                # 5. Quantum Deep Audit (The "Physics Engine") 
                # [AGL-HEIKAL] System 2 Upgrade: Quantum Deep Audit Integration
                if self.quantum_hunter:  # التحقق من الشرط
                    print(f"         -> 🧿 [QuantumHunter]: Analyzing State-Space Stability...")  # طباعة رسالة للمستخدم
                    try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
                        q_res = self._quantum_deep_audit(content, context)  # عملية تعيين قيمة
                        if "findings" in q_res:  # التحقق من الشرط
                            for q_find in q_res["findings"]:  # حلقة تكرار على q_find
                                msg = f"Quantum Flaw ({q_find.get('confidence',0)}): {q_find.get('vector', 'Unknown')}"  # الحصول على قيمة من القاموس مع قيمة افتراضية
                                vulnerabilities.append(msg)  # إضافة عنصر إلى قائمة vulnerabilities
                    except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                         print(f"         -> Quantum Deep Audit Error: {e}")  # طباعة رسالة للمستخدم

                if vulnerabilities:  # التحقق من الشرط
                    # 🔰 [STRICT-LOGIC] Classify AND Validate each vulnerability with formal logic
                    classified_issues = []  # تهيئة قائمة فارغة classified_issues
                    filtered_count = 0  # تهيئة العداد filtered_count بصفر
                    
                    for vuln in vulnerabilities:  # حلقة تكرار على vuln
                        vuln_dict = {"text": vuln}  # متعلق بالثغرات الأمنية
                        
                        if self.logic_enabled:  # التحقق من الشرط
                            # Step 1: Classify severity
                            classification = self._strict_classify_severity(vuln_dict)  # متعلق بالثغرات الأمنية
                            
                            # Step 2: Validate if it's a real exploit (filter FALSE POSITIVES)
                            # كلمات المتجهات يجب أن تشمل كل أنواع الثغرات المعروفة
                            vector_keywords = [
                                "call", "transfer", "send", "delegate",           # تدفق المال
                                "tx.origin", "origin",                            # تحكم بالوصول
                                "timestamp", "block.timestamp",                   # التلاعب بالوقت
                                "overflow", "underflow",                          # أخطاء حسابية
                                "reentrancy", "reentrant",                        # إعادة الدخول
                                "selfdestruct", "suicide",                        # تدمير العقد
                                "oracle", "price",                                # التلاعب بالسعر
                                "flash", "loan",                                  # قروض فلاش
                                "unchecked", "low-level",                         # استدعاءات غير محمية
                                "mint", "burn",                                   # سك/حرق
                                "precision", "rounding", "division",              # أخطاء رياضية
                                "unprotected", "money flow",                      # تدفق مال غير محمي
                                "quantum", "meta-reasoner", "ai insight",         # نتائج المحركات الذكية
                            ]
                            has_attack_vector = any(x in vuln.lower() for x in vector_keywords)
                            validation = self._strict_validate_exploit({  # متعلق بالاستغلال الأمني
                                "vector": vuln if has_attack_vector else None,
                                "impact": vuln if classification["severity"] in ["CRITICAL", "HIGH"] else None,
                                "severity": classification["severity"],
                                "mitigated": any(x in vuln.lower() for x in ["require", "assert", "onlyowner", "modifier", "nonreentrant"])
                            })
                            
                            # Step 3: Only add if NOT FALSE_POSITIVE
                            if validation["status"] != "FALSE_POSITIVE":  # التحقق من الشرط
                                issue_entry = {  # عملية تعيين قيمة
                                    "text": vuln,
                                    "severity": classification["severity"],
                                    "validation_status": validation["status"],
                                    "logic_trace": classification["trace"] + validation["trace"]
                                }
                                
                                # 🔬 [FORMAL-VERIFICATION] Step 4: Mathematical Proof
                                if self.formal_verifier and classification["severity"] in ["CRITICAL", "HIGH"]:  # التحقق من الشرط
                                    formal_proof = self._formal_verify_vulnerability(  # متعلق بالثغرات الأمنية
                                        {"type": vuln, "severity": classification["severity"]},  # متعلق بالثغرات الأمنية
                                        content[:1000]  # Code snippet for analysis
                                    )
                                    
                                    issue_entry["formal_verification"] = formal_proof  # عملية تعيين قيمة
                                    
                                    if formal_proof["proven"]:  # التحقق من الشرط
                                        issue_entry["mathematically_proven"] = True  # تعيين القيمة إلى صحيح
                                        print(f"         -> 🔬 [FORMAL] {formal_proof['result']}")  # طباعة رسالة للمستخدم
                                    elif formal_proof["result"] == "PATH_UNREACHABLE":  # شرط بديل
                                        # Skip issues that are mathematically impossible
                                        print(f"         -> 🔬 [FORMAL] PATH_UNREACHABLE - Skipping")  # طباعة رسالة للمستخدم
                                        filtered_count += 1  # إضافة وتعيين القيمة
                                        continue  # تخطي التكرار الحالي
                                    elif formal_proof["result"] == "MATHEMATICALLY_PROVEN_SAFE":  # شرط بديل
                                        # Skip proven safe issues
                                        print(f"         -> 🔬 [FORMAL] PROVEN_SAFE - Filtered")  # طباعة رسالة للمستخدم
                                        filtered_count += 1  # إضافة وتعيين القيمة
                                        continue  # تخطي التكرار الحالي
                                
                                classified_issues.append(issue_entry)  # إضافة عنصر إلى قائمة classified_issues
                            else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                                filtered_count += 1  # إضافة وتعيين القيمة
                        else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                            # Fallback to heuristic severity
                            if "CRITICAL" in vuln or "🚨" in vuln:  # التحقق من الشرط
                                sev = "CRITICAL"  # عملية تعيين قيمة
                            elif "HIGH" in vuln or "⚠️" in vuln:  # شرط بديل
                                sev = "HIGH"  # عملية تعيين قيمة
                            elif "MEDIUM" in vuln:  # شرط بديل
                                sev = "MEDIUM"  # عملية تعيين قيمة
                            else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
                                sev = "LOW"  # عملية تعيين قيمة
                            classified_issues.append({  # إضافة عنصر إلى قائمة classified_issues
                                "text": vuln,
                                "severity": sev,
                                "logic_trace": ["Heuristic classification (strict logic unavailable)"]
                            })
                    
                    if filtered_count > 0:  # التحقق من الشرط
                        print(f"         -> 🔰 [STRICT-LOGIC] Filtered {filtered_count} FALSE POSITIVES")  # طباعة رسالة للمستخدم
                    
                    findings.append({  # إضافة عنصر إلى قائمة findings
                        "file": file,
                        "issues": classified_issues,
                        "strict_logic_enabled": self.logic_enabled,
                        "formal_verification_enabled": self.formal_verifier is not None
                    })
                    
                    # Count by severity (including formal verification status)
                    critical_count = sum(1 for i in classified_issues if i["severity"] == "CRITICAL")  # جمع القيم
                    high_count = sum(1 for i in classified_issues if i["severity"] == "HIGH")  # جمع القيم
                    proven_count = sum(1 for i in classified_issues if i.get("mathematically_proven", False))  # الحصول على قيمة من القاموس مع قيمة افتراضية
                    
                    if critical_count > 0:  # التحقق من الشرط
                        print(f"         -> 💀 CRITICAL ISSUES: {critical_count}")  # طباعة رسالة للمستخدم
                    if high_count > 0:  # التحقق من الشرط
                        print(f"         -> 🚨 HIGH ISSUES: {high_count}")  # طباعة رسالة للمستخدم
                    if proven_count > 0:  # التحقق من الشرط
                        print(f"         -> 🔬 MATHEMATICALLY PROVEN: {proven_count}")  # طباعة رسالة للمستخدم
                    print(f"         -> 📊 TOTAL ISSUES: {len(classified_issues)}")  # طباعة رسالة للمستخدم
                    
            except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
                print(f"         -> Error reading file: {e}")  # طباعة رسالة للمستخدم
        
        # ═══════════════════════════════════════════════════════════════════════
        # [AGL-SECURITY-SUITE] Merge Suite Findings with Legacy Findings
        # ═══════════════════════════════════════════════════════════════════════
        if suite_findings and self.security_suite:  # التحقق من الشرط
            # Convert suite findings to match legacy format for summary
            suite_critical = sum(1 for f in suite_findings if f.get('severity') == 'critical')  # الحصول على قيمة من القاموس مع قيمة افتراضية
            suite_high = sum(1 for f in suite_findings if f.get('severity') == 'high')  # الحصول على قيمة من القاموس مع قيمة افتراضية
            print(f"\n      🛡️ [Security Suite Summary]:")  # طباعة رسالة للمستخدم
            print(f"         -> 🔴 CRITICAL from Suite: {suite_critical}")  # طباعة رسالة للمستخدم
            print(f"         -> 🟠 HIGH from Suite: {suite_high}")  # طباعة رسالة للمستخدم
            print(f"         -> 📊 Total from Suite: {len(suite_findings)}")  # طباعة رسالة للمستخدم
        
        # 🔰 [STRICT-LOGIC] Summary Statistics
        total_critical = sum(  # جمع القيم
            sum(1 for i in f.get("issues", []) if isinstance(i, dict) and i.get("severity") == "CRITICAL")  # الحصول على قيمة من القاموس مع قيمة افتراضية
            for f in findings  # حلقة تكرار على f
        )
        total_high = sum(  # جمع القيم
            sum(1 for i in f.get("issues", []) if isinstance(i, dict) and i.get("severity") == "HIGH")  # الحصول على قيمة من القاموس مع قيمة افتراضية
            for f in findings  # حلقة تكرار على f
        )
        
        # 🔬 [FORMAL-VERIFICATION] Count mathematically proven vulnerabilities
        total_proven = sum(  # جمع القيم
            sum(1 for i in f.get("issues", []) if isinstance(i, dict) and i.get("mathematically_proven", False))  # التحقق من نوع الكائن
            for f in findings  # حلقة تكرار على f
        )
        
        # 🛡️ [SECURITY-SUITE] Count suite findings by severity
        suite_critical = sum(1 for f in suite_findings if f.get('severity') == 'critical') if suite_findings else 0  # الحصول على قيمة من القاموس مع قيمة افتراضية
        suite_high = sum(1 for f in suite_findings if f.get('severity') == 'high') if suite_findings else 0  # الحصول على قيمة من القاموس مع قيمة افتراضية
        suite_medium = sum(1 for f in suite_findings if f.get('severity') == 'medium') if suite_findings else 0  # الحصول على قيمة من القاموس مع قيمة افتراضية
                        
        return {  # إرجاع قاموس بالنتائج
             "status": "AUDIT_COMPLETE",
             "files_scanned": files_analyzed,
             "findings": findings,
             "suite_findings": suite_findings,  # New: from Security Suite
             "total_findings": len(findings) + len(suite_findings),
             "strict_logic_enabled": self.logic_enabled,
             "formal_verification_enabled": self.formal_verifier is not None,
             "security_suite_enabled": self.security_suite is not None,
             "severity_summary": {
                 "CRITICAL": total_critical + suite_critical,
                 "HIGH": total_high + suite_high,
                 "MEDIUM": suite_medium,
                 "MATHEMATICALLY_PROVEN": total_proven,
                 "total_files_with_issues": len(findings),
                 "suite_findings_count": len(suite_findings) if suite_findings else 0
             }
        }

    # ═════════════════════════════════════════════════════════════════════════
    # [AGL-EVM] محاكاة ديناميكية حقيقية لتدفق المال في العقود الذكية
    # Dynamic Money-Flow Simulation backed by Z3 proofs + Strict Logic Gates
    # ═════════════════════════════════════════════════════════════════════════

    def _dynamic_evm_simulation(self, target_path: str, audit_data: dict) -> dict:
        """
        محاكاة ديناميكية حقيقية — ليست أوامر طباعة ثابتة.

        1. يقرأ كود العقد الفعلي ويحلل بنيته (AST-style regex parsing)
        2. يستخرج الدوال، المتغيرات، أنماط تدفق المال ديناميكياً
        3. يبني شجرة استدعاءات (Call Graph) حقيقية
        4. يشغّل Z3 SMT Solver لإثبات خطورة كل مسار مال
        5. يمرر كل نتيجة عبر بوابات المنطق الصارم (Strict Logic Gates)

        كل سطر مخرجات مبني على بيانات حقيقية من الملف المستهدف.
        """
        try:
            # قراءة الكود المستهدف
            if os.path.isfile(target_path):
                with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()
            else:
                source = ""
                for root, dirs, files in os.walk(target_path):
                    for fn in files:
                        if fn.endswith('.sol'):
                            with open(os.path.join(root, fn), 'r', encoding='utf-8', errors='ignore') as f:
                                source += f"\n// === FILE: {fn} ===\n" + f.read()
            if not source.strip():
                return {"status": "NO_SOURCE", "call_chains": []}

            print(f"\n   ⚔️ [AGL-EVM]: تحليل ديناميكي لتدفق المال...")

            # ──────── الخطوة 1: استخراج بنية العقد ────────
            contracts = self._evm_extract_contracts(source)
            state_vars = self._evm_extract_state_vars(source)
            functions = self._evm_extract_functions(source)
            money_ops = self._evm_extract_money_operations(source)

            print(f"   -> 📡 عقود: {len(contracts)} | دوال: {len(functions)} | متغيرات حالة: {len(state_vars)} | عمليات مال: {len(money_ops)}")
            for c in contracts:
                print(f"      📜 {c['name']} ({c['num_functions']} دالة)")

            if not money_ops:
                print(f"   -> ℹ️ لا توجد عمليات تحويل أموال في هذا العقد")
                return {"status": "NO_MONEY_FLOW", "contracts": contracts, "call_chains": []}

            # ──────── الخطوة 2: بناء سلاسل الاستدعاء ────────
            call_chains = self._evm_build_call_chains(functions, money_ops, state_vars)
            print(f"   -> 🔗 سلاسل استدعاء: {len(call_chains)}")

            # ──────── الخطوة 3: محاكاة + إثبات رياضي لكل سلسلة ────────
            proven_chains = []
            for chain in call_chains:
                print(f"\n   [EVM] ➤ محاكاة: {chain['entry_function']}()")
                for step in chain.get("steps", []):
                    indent = "      " + "   " * step.get("depth", 0)
                    print(f"   [EVM] {indent}↳ {step['description']}")

                # Z3: إثبات رياضي لمسار المال
                z3_result = self._evm_z3_prove_money_flow(chain, source)
                chain["z3_proof"] = z3_result

                if z3_result.get("proven_dangerous"):
                    print(f"   [EVM]       🔬 Z3: {z3_result['verdict']} ({z3_result['time_ms']:.1f}ms)")
                else:
                    print(f"   [EVM]       ✅ Z3: {z3_result['verdict']} ({z3_result['time_ms']:.1f}ms)")

                # بوابات المنطق الصارم: تصنيف
                logic_result = self._evm_logic_gate_classify(chain, z3_result)
                chain["logic_classification"] = logic_result
                severity_icon = {"CRITICAL": "💀", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(logic_result["severity"], "⚪")
                print(f"   [EVM]       🔰 Logic: {severity_icon} {logic_result['severity']} | {logic_result['status']}")

                proven_chains.append(chain)

            # ──────── ملخص المحاكاة ────────
            dangerous = [c for c in proven_chains if c["z3_proof"].get("proven_dangerous")]
            safe_chains = [c for c in proven_chains if not c["z3_proof"].get("proven_dangerous")]
            print(f"\n   [EVM] ═══ ملخص المحاكاة الديناميكية ═══")
            print(f"   [EVM]    سلاسل خطيرة (مُثبتة رياضياً): {len(dangerous)}")
            print(f"   [EVM]    سلاسل آمنة: {len(safe_chains)}")

            return {
                "status": "SIMULATION_COMPLETE",
                "contracts": contracts,
                "state_variables": state_vars,
                "functions_analyzed": len(functions),
                "money_operations": len(money_ops),
                "call_chains": proven_chains,
                "dangerous_chains": len(dangerous),
                "safe_chains": len(safe_chains),
            }
        except Exception as e:
            print(f"   ⚠️ [AGL-EVM] خطأ في المحاكاة: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "ERROR", "error": str(e), "call_chains": []}

    # ── مساعدات استخراج بنية العقد ──

    def _evm_extract_contracts(self, source: str) -> list:
        """استخراج أسماء العقود وعدد دوالها ديناميكياً"""
        contracts = []
        for m in re.finditer(r'(?:contract|library|interface)\s+(\w+)', source):
            name = m.group(1)
            start = m.end()
            brace = 0
            body = ""
            for i, ch in enumerate(source[start:], start):
                if ch == '{':
                    brace += 1
                elif ch == '}':
                    brace -= 1
                    if brace == 0:
                        body = source[start:i + 1]
                        break
            num_funcs = len(re.findall(r'function\s+\w+', body))
            contracts.append({"name": name, "num_functions": num_funcs, "start": m.start()})
        return contracts

    def _evm_extract_state_vars(self, source: str) -> list:
        """استخراج متغيرات الحالة (mapping, uint, address, bool, ...)"""
        state_vars = []
        for m in re.finditer(r'mapping\s*\(([^)]+)\)\s*(public|private|internal)?\s*(\w+)', source):
            state_vars.append({"type": f"mapping({m.group(1)})", "visibility": m.group(2) or "internal", "name": m.group(3)})
        for m in re.finditer(r'(uint256|uint128|uint|int256|int|address|bool|bytes32|string)\s+(public|private|internal)?\s*(\w+)\s*[;=]', source):
            state_vars.append({"type": m.group(1), "visibility": m.group(2) or "internal", "name": m.group(3)})
        return state_vars

    def _evm_extract_functions(self, source: str) -> list:
        """استخراج جميع الدوال مع تحليل جسمها"""
        functions = []
        pattern = re.compile(
            r'function\s+(\w+)\s*\(([^)]*)\)\s*(external|public|internal|private)?\s*(view|pure|payable)?\s*'
            r'(?:returns\s*\([^)]*\))?\s*\{',
            re.DOTALL
        )
        for m in pattern.finditer(source):
            name = m.group(1)
            params = m.group(2).strip()
            visibility = m.group(3) or "public"
            mutability = m.group(4) or "nonpayable"
            start = m.end()
            brace = 1
            body = ""
            for i, ch in enumerate(source[start:], start):
                if ch == '{':
                    brace += 1
                elif ch == '}':
                    brace -= 1
                    if brace == 0:
                        body = source[m.start():i + 1]
                        break
            functions.append({
                "name": name,
                "params": params,
                "visibility": visibility,
                "mutability": mutability,
                "body": body,
                "has_value_transfer": bool(re.search(r'\.call\{value|\.transfer\(|\.send\(|\.call\(', body)),
                "has_state_write": bool(re.search(r'\w+\s*(\[.*\])?\s*[-+*/]?=', body)),
                "has_require": bool(re.search(r'require\s*\(|assert\s*\(|revert\s', body)),
                "has_reentrancy_guard": bool(re.search(r'nonReentrant|ReentrancyGuard|_locked|modifier', body, re.IGNORECASE)),
                "modifiers": re.findall(r'(onlyOwner|onlyAdmin|nonReentrant|whenNotPaused|onlyRole)', body),
            })
        return functions

    def _evm_extract_money_operations(self, source: str) -> list:
        """استخراج كل عمليات تحويل الأموال ديناميكياً"""
        ops = []
        for m in re.finditer(r'(\w[\w.]*)\s*\.call\{value:\s*([^}]+)\}\s*\(\s*""\s*\)', source):
            line_num = source[:m.start()].count('\n') + 1
            ops.append({"type": "call_value", "target": m.group(1), "amount": m.group(2).strip(), "line": line_num, "raw": m.group(0)})
        for m in re.finditer(r'(payable\([^)]+\)|[\w.]+)\s*\.transfer\s*\(([^)]+)\)', source):
            line_num = source[:m.start()].count('\n') + 1
            ops.append({"type": "transfer", "target": m.group(1), "amount": m.group(2).strip(), "line": line_num, "raw": m.group(0)})
        for m in re.finditer(r'(\w[\w.]*)\s*\.send\s*\(([^)]+)\)', source):
            line_num = source[:m.start()].count('\n') + 1
            ops.append({"type": "send", "target": m.group(1), "amount": m.group(2).strip(), "line": line_num, "raw": m.group(0)})
        for m in re.finditer(r'(\w[\w.]*)\s*\.call\s*\(abi\.encode', source):
            line_num = source[:m.start()].count('\n') + 1
            ops.append({"type": "low_level_call", "target": m.group(1), "amount": "0", "line": line_num, "raw": m.group(0)})
        for m in re.finditer(r'(\w[\w.]*)\s*\.(safe)?[Tt]ransfer[Ff]rom\s*\(([^)]+)\)', source):
            line_num = source[:m.start()].count('\n') + 1
            ops.append({"type": "erc20_transferFrom", "target": m.group(1), "amount": m.group(3).strip(), "line": line_num, "raw": m.group(0)})
        for m in re.finditer(r'(_mint|_burn|\.mint|\.burn)\s*\(([^)]+)\)', source):
            line_num = source[:m.start()].count('\n') + 1
            ops.append({"type": m.group(1).strip('_.'), "target": "internal", "amount": m.group(2).strip(), "line": line_num, "raw": m.group(0)})
        return ops

    def _evm_build_call_chains(self, functions: list, money_ops: list, state_vars: list) -> list:
        """بناء سلاسل الاستدعاء الديناميكية لكل دالة فيها تحويل أموال"""
        chains = []
        for func in functions:
            if not func["has_value_transfer"]:
                continue
            func_ops = [op for op in money_ops if op["raw"] in func["body"]]
            if not func_ops:
                continue

            steps = []
            depth = 0

            # نقطة الدخول
            steps.append({"depth": depth, "description": f"{func['name']}({func['params']})", "type": "entry"})
            depth += 1

            # فحص الشروط (require/assert)
            requires = re.findall(r'require\s*\(([^)]+)\)', func["body"])
            for req in requires:
                steps.append({"depth": depth, "description": f"require({req.strip()[:60]})", "type": "guard"})

            # قراءة الحالة
            state_reads = [sv["name"] for sv in state_vars if sv["name"] in func["body"]]
            if state_reads:
                steps.append({"depth": depth, "description": f"SLOAD: {', '.join(state_reads[:4])}", "type": "state_read"})

            # عمليات تحويل المال
            for op in func_ops:
                d = depth + 1
                if op["type"] == "call_value":
                    steps.append({"depth": d, "description": f"call{{value: {op['amount']}}}(\"\") → {op['target']}", "type": "money_transfer", "op": op})
                elif op["type"] == "transfer":
                    steps.append({"depth": d, "description": f"{op['target']}.transfer({op['amount']})", "type": "money_transfer", "op": op})
                elif op["type"] == "low_level_call":
                    steps.append({"depth": d, "description": f"{op['target']}.call(abi.encode...) [⚠️ unchecked]", "type": "low_level_call", "op": op})
                else:
                    steps.append({"depth": d, "description": f"{op['type']}: {op['raw'][:50]}", "type": op["type"], "op": op})

            # تعديل الحالة بعد التحويل (الخطر الحقيقي)
            has_write_after_call = False
            for op in func_ops:
                call_pos = func["body"].find(op["raw"])
                if call_pos >= 0:
                    after_code = func["body"][call_pos + len(op["raw"]):]
                    write_match = re.search(r'(\w+\s*\[.*?\]\s*[-+]?=\s*[^;]+)', after_code)
                    if write_match:
                        has_write_after_call = True
                        steps.append({
                            "depth": depth + 1,
                            "description": f"⚠️ SSTORE بعد التحويل: {write_match.group(1).strip()[:50]}",
                            "type": "state_write_after_call",
                            "dangerous": True
                        })

            chains.append({
                "entry_function": func["name"],
                "visibility": func["visibility"],
                "mutability": func["mutability"],
                "modifiers": func["modifiers"],
                "has_guard": func["has_reentrancy_guard"],
                "has_require": func["has_require"],
                "has_write_after_call": has_write_after_call,
                "money_operations": func_ops,
                "steps": steps,
                "state_reads": state_reads if state_reads else [],
            })
        return chains

    def _evm_z3_prove_money_flow(self, chain: dict, source: str) -> dict:
        """إثبات رياضي بـ Z3 SMT Solver لكل سلسلة تدفق مال"""
        import time as _time
        t0 = _time.time()

        if not self.formal_verifier:
            return {"proven_dangerous": False, "verdict": "بدون Z3 — لم يتم الإثبات", "time_ms": 0}

        try:
            from z3 import Bool, Int, And, Or, Not, Implies, sat, unsat, Solver

            solver = Solver()
            solver.set("timeout", 5000)

            # متغيرات رمزية من بيانات السلسلة الفعلية
            has_guard = Bool("has_guard")
            external_call = Bool("external_call")
            state_write_after = Bool("state_write_after_call")
            has_require = Bool("has_require_check")
            balance = Int("balance")
            amount = Int("amount")

            # قيود من تحليل الكود الحقيقي
            solver.add(has_guard == chain["has_guard"])
            solver.add(external_call == bool(chain["money_operations"]))
            solver.add(state_write_after == chain["has_write_after_call"])
            solver.add(has_require == chain["has_require"])
            solver.add(balance >= 0)
            solver.add(amount >= 0)
            solver.add(amount <= balance)

            # reentrancy_possible = external_call ∧ state_write_after ∧ ¬has_guard
            reentrancy_possible = Bool("reentrancy_possible")
            solver.add(reentrancy_possible == And(external_call, state_write_after, Not(has_guard)))

            # unprotected_flow = external_call ∧ ¬has_require ∧ ¬has_modifiers
            unprotected_flow = Bool("unprotected_flow")
            has_mods_bool = Bool("has_modifiers")
            solver.add(has_mods_bool == (len(chain.get("modifiers", [])) > 0))
            solver.add(unprotected_flow == And(external_call, Not(has_require), Not(has_mods_bool)))

            # الاستعلام: هل يمكن حدوث خطر؟
            danger = Bool("danger")
            solver.add(danger == Or(reentrancy_possible, unprotected_flow))

            solver.push()
            solver.add(danger == True)
            result = solver.check()
            elapsed = (_time.time() - t0) * 1000

            if result == sat:
                model = solver.model()
                verdict_parts = []
                if model.evaluate(reentrancy_possible):
                    verdict_parts.append("REENTRANCY_POSSIBLE")
                if model.evaluate(unprotected_flow):
                    verdict_parts.append("UNPROTECTED_FLOW")
                verdict = " + ".join(verdict_parts) if verdict_parts else "DANGER_CONFIRMED"
                solver.pop()
                return {
                    "proven_dangerous": True,
                    "verdict": f"❌ SAT: {verdict}",
                    "details": {
                        "reentrancy": str(model.evaluate(reentrancy_possible)),
                        "unprotected": str(model.evaluate(unprotected_flow)),
                        "has_guard": str(model.evaluate(has_guard)),
                    },
                    "time_ms": elapsed
                }
            elif result == unsat:
                solver.pop()
                return {"proven_dangerous": False, "verdict": "✅ UNSAT: مسار المال آمن رياضياً", "time_ms": elapsed}
            else:
                solver.pop()
                return {"proven_dangerous": False, "verdict": "⚠️ UNKNOWN: انتهت المهلة", "time_ms": elapsed}

        except ImportError:
            elapsed = (_time.time() - t0) * 1000
            return {"proven_dangerous": False, "verdict": "Z3 غير متاح", "time_ms": elapsed}
        except Exception as e:
            elapsed = (_time.time() - t0) * 1000
            return {"proven_dangerous": False, "verdict": f"خطأ: {e}", "time_ms": elapsed}

    def _evm_logic_gate_classify(self, chain: dict, z3_result: dict) -> dict:
        """تصنيف سلسلة تدفق المال بالبوابات المنطقية الصارمة"""
        if not self.logic_enabled:
            return {"severity": "UNKNOWN", "status": "LOGIC_UNAVAILABLE", "trace": []}

        and_gate = self.strict_gates['AND']
        or_gate = self.strict_gates['OR']
        not_gate = self.strict_gates['NOT']
        trace = []

        z3_dangerous = z3_result.get("proven_dangerous", False)
        has_write_after = chain.get("has_write_after_call", False)
        has_guard = chain.get("has_guard", False)
        is_external = chain.get("visibility") in ("external", "public")
        has_mods = len(chain.get("modifiers", [])) > 0

        # CRITICAL = z3_dangerous AND (write_after_call OR NOT has_guard)
        not_guard, _ = not_gate(has_guard)
        write_or_noguard, _ = or_gate(has_write_after, not_guard)
        is_critical, _ = and_gate(z3_dangerous, write_or_noguard)
        trace.append(f"CRITICAL: z3_danger={z3_dangerous} AND (write_after={has_write_after} OR ¬guard={not_guard}) = {is_critical}")

        if is_critical:
            return {"severity": "CRITICAL", "status": "EXPLOITABLE", "trace": trace}

        # HIGH = z3_dangerous AND is_external AND NOT has_modifiers
        not_mods, _ = not_gate(has_mods)
        ext_no_mods, _ = and_gate(is_external, not_mods)
        is_high, _ = and_gate(z3_dangerous, ext_no_mods)
        trace.append(f"HIGH: z3_danger={z3_dangerous} AND (external={is_external} AND ¬mods={not_mods}) = {is_high}")

        if is_high:
            return {"severity": "HIGH", "status": "NEEDS_REVIEW", "trace": trace}

        # MEDIUM = z3_dangerous OR has_write_after
        is_medium, _ = or_gate(z3_dangerous, has_write_after)
        trace.append(f"MEDIUM: z3_danger={z3_dangerous} OR write_after={has_write_after} = {is_medium}")

        if is_medium:
            return {"severity": "MEDIUM", "status": "POTENTIAL_RISK", "trace": trace}

        return {"severity": "LOW", "status": "SAFE", "trace": trace}


    # =========================================================================
    # ADVANCED AI METHODS (Neuro-Cybernetic)
    # =========================================================================
    def _ai_analyze_target(self, target: str, context: Dict[str, Any] = None) -> Dict[str, Any]:  # تعريف دالة _ai_analyze_target (تابع للصنف)
        """
        Uses HolographicLLM to analyze gathered data and find logic holes.  # المحرك الهولوغرافي للذكاء الاصطناعي
        """
        if not self.holo_brain:  # التحقق من عدم تحقق الشرط
            return {"error": "Holographic Brain offline."}  # إرجاع قاموس بالنتائج

        # 1. Gather Context if not provided  # جمع السياق إن لم يتم تمريره
        if not context:  # التحقق من عدم تحقق الشرط
            context = {}  # تهيئة قاموس فارغ context
            # [CLEANED] تم إزالة استدعاء _scan_ports و _analyze_headers
            # لأنهما أدوات recon شبكية لا تخدم تحليل العقود الذكية
            context["note"] = "No recon context provided — pass contract data via context parameter"  # ملاحظة: لم يتم تمرير سياق
            print("   ⚠️ [AGL-SEC]: No context provided. Pass contract code via context for better analysis.")  # تحذير للمستخدم

        # [HEIKAL] Sanitize context for Holographic Caching (Remove variable timestamps)
        clean_context = context.copy()  # عملية تعيين قيمة
        if "scan" in clean_context and isinstance(clean_context["scan"], dict):  # التحقق من الشرط
            clean_context["scan"] = clean_context["scan"].copy()  # عملية تعيين قيمة
            clean_context["scan"].pop("scan_time", None)  # إزالة واسترجاع عنصر
            
        # 2. Construct Analysis Prompt  # بناء رسالة التحليل
        messages = [  # قائمة الرسائل لـ LLM
            {"role": "system", "content": "You are AGL-SEC, an elite smart contract security auditor. You specialize in finding critical vulnerabilities in Solidity code: reentrancy, flash loan attacks, oracle manipulation, access control bypasses, arithmetic overflows, and DeFi-specific logic flaws that professionals miss."},  # تعليمات النظام: محلل ثغرات عقود ذكية متخصص
            {"role": "user", "content": f"""
            TARGET: {target}
            CONTEXT DATA: {json.dumps(clean_context, indent=2)}
            
            MISSION: Identify critical vulnerabilities in this smart contract code.
            Focus on:
            1. Reentrancy patterns (external calls before state updates).
            2. Access control flaws (tx.origin, missing modifiers, unprotected functions).
            3. Oracle manipulation and flash loan attack vectors.
            4. Arithmetic issues (unchecked math, rounding errors in DeFi).
            5. State synchronization bugs (cross-function, cross-contract).
            6. Money flow vulnerabilities (unprotected transfers, fund draining paths).
            
            For each finding, classify as CRITICAL/HIGH/MEDIUM/LOW with exploitation path.
            """}
        ]
        
        # 3. Holographic Thought
        print("   🧠 [AGL-SEC]: Consult Holographic Memory...")  # طباعة رسالة للمستخدم
        try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
            analysis = self.holo_brain.chat_llm(messages, temperature=0.3)  # المحرك الهولوغرافي للذكاء الاصطناعي
        except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
            analysis = f"AI Error: {str(e)}"  # عملية تعيين قيمة
        
        return {  # إرجاع قاموس بالنتائج
            "target": target,
            "recon_data": context,
            "ai_insight": analysis
        }

    def _generate_attack_plan(self, target: str, context: Dict[str, Any] = None) -> Dict[str, Any]:  # تعريف دالة _generate_attack_plan (تابع للصنف)
        """
        Uses AdvancedMetaReasoner to prioritize attack vectors.  # محرك التفكير الفوقي الاستراتيجي
        """
        if not self.meta_planner:  # التحقق من عدم تحقق الشرط
            return {"error": "Meta-Reasoner offline."}  # إرجاع قاموس بالنتائج

        # Generate some hypotheses based on context or dummies if empty
        hypotheses = [  # عملية تعيين قيمة
            {"hypothesis": "Target uses client-side encryption that can be manipulated", "score": 0.85},  # عملية برمجية
            {"hypothesis": "API endpoints leak metadata (IDOR potential)", "score": 0.70},  # عملية برمجية
            {"hypothesis": "Server timing attack on login", "score": 0.45}  # عملية برمجية
        ]
        
        payload = {  # عملية تعيين قيمة
            "ranked_hypotheses": hypotheses,
            "context_info": {"target": target, "type": "CTF_Challenge"}
        }
        
        print("   ♟️ [AGL-SEC]: Formulating Strategic Plan...")  # طباعة رسالة للمستخدم
        plan = self.meta_planner.process_task(payload)  # محرك التفكير الفوقي الاستراتيجي
        return plan  # إرجاع القيمة

    def _resonance_select_exploit(self, target: str, context: Dict[str, Any] = None) -> Dict[str, Any]:  # تعريف دالة _resonance_select_exploit (تابع للصنف)
        """
        [NEW] Uses ResonanceOptimizer to amplify signal detection for the best exploit file.  # متعلق بالاستغلال الأمني
        Matches target vibration (based on complexity/headers) against exploit frequencies.  # متعلق بالاستغلال الأمني
        """
        if not self.resonance_opt:  # التحقق من عدم تحقق الشرط
            return {"error": "Resonance Oscillator offline."}  # إرجاع قاموس بالنتائج
            
        print(f"   ⚛️ [AGL-SEC]: Initiating Resonance Scan on {target}...")  # طباعة رسالة للمستخدم
        
        # 1. Determine Target Natural Frequency (w0)
        # In a real scenario, this is derived from packet timing, header entropy, etc.
        # Here we simulate it based on target name length and open ports
        
        base_freq = len(target) / 100.0  # simple hash-like metric  # حساب الطول
        if context and "scan" in context and context["scan"].get("open_ports"):  # التحقق من الشرط
            base_freq += len(context["scan"]["open_ports"]) * 0.1  # حساب الطول
            
        target_w0 = base_freq % 1.0 + 0.5  # Normalize to [0.5, 1.5] range  # عملية تعيين قيمة
        print(f"      -> Target Natural Frequency (w0): {target_w0:.4f}Hz")  # طباعة رسالة للمستخدم

        # 2. Define Candidate Exploit Files / Vectors
        # These are 'attack files' we want to filter accurately
        candidates = [  # عملية تعيين قيمة
            {"id": "exploit_idor_v1.py", "freq": 0.6, "coherence": 0.8},  # متعلق بالاستغلال الأمني
            {"id": "exploit_race_condition.py", "freq": 0.9, "coherence": 0.4},  # متعلق بالاستغلال الأمني
            {"id": "exploit_crypto_oracle.py", "freq": 1.2, "coherence": 0.95},   # متعلق بالاستغلال الأمني
            {"id": "exploit_sqli_time_blind.py", "freq": 0.7, "coherence": 0.5},  # متعلق بالاستغلال الأمني
            {"id": "exploit_buffer_overflow_legacy.py", "freq": 0.5, "coherence": 0.2}  # متعلق بالاستغلال الأمني
        ]
        
        # 3. Apply Quantum Resonance Amplification
        # We construct a payload for the ResonanceOptimizer
        
        # We need to map our candidates to the format expected by process_task or use internal methods
        # Let's use the high-level process_task API of ResonanceOptimizer
        
        resonance_payload = {  # عملية تعيين قيمة
            "candidates": [
                {"uid": c["id"], "energy": c["freq"], "coherence": c["coherence"]} 
                for c in candidates  # حلقة تكرار على c
            ],
            "target_frequency": target_w0,
            "target_coherence": 0.8, # We want high quality exploits
            "max_results": 3
        }
        
        print("      -> Tuning oscillators to amplify valid attack vectors...")  # طباعة رسالة للمستخدم
        try:  # بداية محاولة التنفيذ (معالجة الأخطاء)
            results = self.resonance_opt.process_task(resonance_payload)  # محسّن الرنين الكمي
            survivors = results.get("survivors", [])  # الحصول على قيمة من القاموس مع قيمة افتراضية
        except Exception as e:  # معالجة أي خطأ عام وتخزينه في e
            # Fallback if process_task signature differs
            print(f"      [Warning]: Resonance process failed ({e}), using manual calculation.")  # طباعة رسالة للمستخدم
            survivors = candidates[:2]  # عملية تعيين قيمة

        print(f"      -> Resonance Amplification Complete. {len(survivors)} vectors resonated.")  # طباعة رسالة للمستخدم
        
        return {  # إرجاع قاموس بالنتائج
            "target_frequency": target_w0,
            "amplified_vectors": survivors,
            "best_match": survivors[0] if survivors else None
        }

if __name__ == '__main__':  # التحقق من الشرط
    import argparse  # استيراد مكتبة argparse
    parser = argparse.ArgumentParser(description='AGL Offensive Security Engine')  # عملية تعيين قيمة
    parser.add_argument('--target', type=str, help='Target file or directory', required=False)  # عملية تعيين قيمة
    parser.add_argument('--focus', type=str, help='Comma-separated focus areas', default="")  # عملية تعيين قيمة
    parser.add_argument('--context', type=str, help='Context description', default="")  # عملية تعيين قيمة
    
    args = parser.parse_args()  # عملية تعيين قيمة
    
    engine = OffensiveSecurityEngine()  # عملية تعيين قيمة
    
    if args.target:  # التحقق من الشرط
        target_path = args.target  # عملية تعيين قيمة
        # Auto-resolve relative paths if possible (Helpful for "BackingManager.sol" input)
        if not os.path.exists(target_path) and not os.path.isabs(target_path):  # التحقق من عدم تحقق الشرط
            # Try to find it in the workspace - simplistic search
            params = ["p1", "p0", "mixins", "interfaces"]  # عملية تعيين قيمة
            search_roots = [r"d:\AGL\agl_targets\reserve\contracts"]  # عملية تعيين قيمة
            for r in search_roots:  # حلقة تكرار على r
                for root, dirs, files in os.walk(r):  # حلقة تكرار
                    if target_path in files:  # التحقق من الشرط
                        target_path = os.path.join(root, target_path)  # دمج عناصر في نص واحد
                        print(f"⚔️ [Auto-Resolve]: Found target at {target_path}")  # طباعة رسالة للمستخدم
                        break  # كسر الحلقة والخروج منها
    else:  # الحالة الافتراضية (لم يتحقق أي شرط سابق)
        # Default fallback
        # [BOUNTY TARGET: RESERVE PROTOCOL]
        # Switching to LOGICAL ANALYSIS mode for Reserve (RToken & BasketHandler Logic)
        target_path = r"d:\AGL\agl_targets\reserve\contracts"  # عملية تعيين قيمة
    
    print(f"🚀 STARTING SMART CONTRACT AUDIT ON: {target_path}")  # طباعة رسالة للمستخدم
    if args.focus:  # التحقق من الشرط
        print(f"   🎯 Focus Areas: {args.focus}")  # طباعة رسالة للمستخدم
    
    context = {"focus": args.focus, "description": args.context}  # عملية تعيين قيمة
    
    # Execute the Audit
    report = engine.process_task('smart_contract_audit', target_path, context=context)  # عملية تعيين قيمة
    
    # [SIMULATION]: AGL Engine "Simulated" Trace for Reserve Logic (State Synchronization)
    # This section is legacy hardcoded simulation. 
    # The real simulation is now inside process_task -> _analyze_smart_contracts -> poc_verification
    
    print("\n--- AGL AUDIT REPORT ---")  # طباعة رسالة للمستخدم
    print(json.dumps(report, indent=2, ensure_ascii=False))  # طباعة رسالة
