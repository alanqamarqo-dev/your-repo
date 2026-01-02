# 🔗 خريطة ترابط ملفات نظام AGL

النظام يعمل كشبكة مترابطة، وهذه هي نقاط الاتصال الرئيسية:

## 1. العقل المدبر (Physics & Consciousness Hub)
**الملف:** `d:\AGL\AGL_Core\Heikal_Quantum_Core.py`
هذا هو "القلب" الذي يربط الفيزياء بالوعي.
*   **يستورد:**
    *   `VectorizedWaveProcessor` (للسرعة الفيزيائية).
    *   `MoralReasoner` (للأخلاق).
    *   `SelfModel` (للوعي).
    *   `ResonanceOptimizer` (للتناغم).
*   **وظيفته:** اتخاذ القرارات "الشبحية" (Ghost Decisions) بناءً على تداخل الموجات والقيم الأخلاقية.

## 2. سجل المحركات (The Registry)
**الملف:** `d:\AGL\repo-copy\Core_Engines\__init__.py`
هذا هو "دليل الهاتف" للنظام.
*   **يحتوي على:** قائمة `ENGINE_SPECS` التي تعرف مكان كل محرك (مثل `Mathematical_Brain`, `Hive_Mind`, `Volition_Engine`).
*   **وظيفته:** عندما يطلب النظام "محرك الإرادة"، هذا الملف يخبره أين يجده.

## 3. المشغل الرئيسي (The Agent Loop)
**الملف:** `d:\AGL\autonomous_agent.py`
هذا هو "الجسد" الذي يتحرك وينفذ المهام.
*   **يستورد:** `Heikal_Quantum_Core` والمحركات الأخرى عبر `agl_paths`.
*   **وظيفته:** حلقة لا نهائية (Loop) تستقبل الأوامر، تفكر، وتنفذ باستخدام المحركات المتاحة.

## 4. المحرك الفيزيائي السريع (The Engine Room)
**الملف:** `d:\AGL\AGL_Vectorized_Wave_Processor.py`
هذا هو "المحرك التوربيني".
*   **وظيفته:** تنفيذ ملايين العمليات الحسابية المعقدة (مصفوفات NumPy) في جزء من الثانية لخدمة `Heikal_Quantum_Core`.

---

### 🔄 كيف تتدفق البيانات؟
1.  **الطلب:** يأتي عبر `autonomous_agent.py`.
2.  **المعالجة:** يتم إرساله إلى `Heikal_Quantum_Core.py`.
3.  **الفيزياء:** النواة تطلب من `VectorizedWaveProcessor.py` حساب الموجات.
4.  **الأخلاق:** النواة تطلب من `MoralReasoner` التحقق من النية.
5.  **القرار:** النتيجة تعود إلى `autonomous_agent.py` للتنفيذ.
