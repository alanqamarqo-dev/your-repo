# AGL Information Flow Architecture / هندسة تدفق المعلومات في AGL

**Developer / المطور:** Hossam Heikal (حسام هيكل)
**Date / التاريخ:** December 13, 2025

---

## 1. Overview / نظرة عامة

### English

The AGL system operates on a cyclic information flow model designed to mimic conscious cognitive processes. Data does not merely pass through; it is perceived, contextualized, processed, and stored. The flow is orchestrated by the **Integration Layer** and supported by the **Conscious Bridge**.

### العربية

يعمل نظام AGL بناءً على نموذج تدفق معلومات دوري مصمم لمحاكاة العمليات المعرفية الواعية. البيانات لا تمر فقط؛ بل يتم إدراكها، ووضعها في سياق، ومعالجتها، وتخزينها. يتم تنسيق التدفق بواسطة **طبقة التكامل (Integration Layer)** وبدعم من **جسر الوعي (Conscious Bridge)**.

---

## 2. Perception & Input / الإدراك والمدخلات

 English

**Source:** User Input, Web Search, System Sensors.

1. **Perception Loop (`Core_Consciousness/Perception_Loop.py`)**: Raw data is captured from the environment or user interface.
2. **Normalization**: Inputs are converted to a standard JSON format to ensure consistency across engines.
3. **Intent Recognition**: The `Volition_Engine` analyzes the input to determine if it aligns with current goals or requires a new drive (e.g., curiosity, preservation).

 العربية

**المصدر:** مدخلات المستخدم، البحث على الويب، مستشعرات النظام.

1. **حلقة الإدراك (`Core_Consciousness/Perception_Loop.py`)**: يتم التقاط البيانات الخام من البيئة أو واجهة المستخدم.
2. **التطبيع (Normalization)**: يتم تحويل المدخلات إلى تنسيق JSON قياسي لضمان الاتساق عبر المحركات.
3. **التعرف على النوايا**: يقوم `Volition_Engine` بتحليل المدخلات لتحديد ما إذا كانت تتماشى مع الأهداف الحالية أو تتطلب دافعًا جديدًا (مثل الفضول، الحفاظ على الذات).

---

## 3. Routing & Contextualization / التوجيه والسياق

 English

**Component:** `Integration_Layer`

1. **Global Context**: The input is merged with the `Global_Context` to add historical relevance and current system state.
2. **Action Router (`Action_Router.py`)**: The system decides which engine is best suited for the task.
    * *Logic/Math* -> `Mathematical_Brain`
    * *Conversation* -> `Hosted_LLM`
    * *Coding* -> `Code_Generator`
3. **Prompt Composition (`Hybrid_Composer.py`)**: A specialized prompt is built, injecting relevant memories, safety constraints, and specific instructions for the target engine.

 العربية

**المكون:** `Integration_Layer`

1. **السياق العالمي**: يتم دمج المدخلات مع `Global_Context` لإضافة الصلة التاريخية وحالة النظام الحالية.
2. **موجه الإجراءات (`Action_Router.py`)**: يقرر النظام أي محرك هو الأنسب للمهمة.
    * *منطق/رياضيات* -> `Mathematical_Brain`
    * *محادثة* -> `Hosted_LLM`
    * *برمجة* -> `Code_Generator`
3. **تكوين المطالبة (`Hybrid_Composer.py`)**: يتم بناء مطالبة متخصصة، مع حقن الذكريات ذات الصلة، وقيود الأمان، وتعليمات محددة للمحرك المستهدف.

---

## 4. Cognitive Processing / المعالجة المعرفية

 English

**Component:** `Core_Engines`
The selected engine processes the request.

* **LLM Processing**: If language generation is required, the `Hosted_LLM` calls the model (Ollama/OpenAI) with the composed prompt.
* **Reasoning**: The `Inference_Engine` checks for logical consistency and potential fallacies.
* **Safety Check**: The `Safety_Control_Layer` inspects the generated output *before* it is finalized to ensure it adheres to `Core_Values_Lock`.

 العربية

**المكون:** `Core_Engines`
يقوم المحرك المختار بمعالجة الطلب.

* **معالجة LLM**: إذا كان توليد اللغة مطلوبًا، يقوم `Hosted_LLM` باستدعاء النموذج (Ollama/OpenAI) مع المطالبة المركبة.
* **التفكير**: يتحقق `Inference_Engine` من الاتساق المنطقي والمغالطات المحتملة.
* **فحص الأمان**: تقوم `Safety_Control_Layer` بفحص المخرجات التي تم إنشاؤها *قبل* اعتمادها نهائيًا للتأكد من التزامها بـ `Core_Values_Lock`.

---

## 5. Memory Consolidation / دمج الذاكرة

 English

**Component:** `Core_Memory` & `Conscious_Bridge`

1. **Short-Term Memory**: The interaction is stored in the active session context for immediate reference.
2. **Conscious Bridge**: Significant events are passed to the `Conscious_Bridge`, which acts as the gateway to long-term storage.
3. **Long-Term Storage**: During the `Dreaming_Cycle` (idle time), important patterns and lessons are moved to the `Knowledge_Base` (SQLite/JSONL) to be available for future sessions.

 العربية

**المكون:** `Core_Memory` و `Conscious_Bridge`

1. **الذاكرة قصيرة المدى**: يتم تخزين التفاعل في سياق الجلسة النشطة للرجوع إليه فورًا.
2. **جسر الوعي**: يتم تمرير الأحداث الهامة إلى `Conscious_Bridge`، الذي يعمل كبوابة للتخزين طويل المدى.
3. **التخزين طويل المدى**: أثناء `Dreaming_Cycle` (وقت الخمول)، يتم نقل الأنماط والدروس المهمة إلى `Knowledge_Base` (SQLite/JSONL) لتكون متاحة للجلسات المستقبلية.

---

## 6. Feedback & Evolution / التغذية الراجعة والتطور

 English

**Component:** `Learning_System`

1. **Outcome Analysis**: The `Feedback_Analyzer` compares the actual result against the expected goal.
2. **Self-Correction**: If the result is suboptimal, the `Recursive_Improver` may suggest code changes or prompt adjustments to prevent future errors.
3. **Evolution**: Successful strategies are reinforced in `Learned_Patterns.json`, effectively "teaching" the system how to handle similar situations better next time.

 العربية

**المكون:** `Learning_System`

1. **تحليل النتائج**: يقوم `Feedback_Analyzer` بمقارنة النتيجة الفعلية بالهدف المتوقع.
2. **التصحيح الذاتي**: إذا كانت النتيجة دون المستوى الأمثل، قد يقترح `Recursive_Improver` تغييرات في الكود أو تعديلات في المطالبات لمنع الأخطاء المستقبلية.
3. **التطور**: يتم تعزيز الاستراتيجيات الناجحة في `Learned_Patterns.json`، مما "يعلم" النظام فعليًا كيفية التعامل مع المواقف المماثلة بشكل أفضل في المرة القادمة.
