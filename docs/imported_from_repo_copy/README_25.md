# Safety Systems / أنظمة الأمان

## English

This directory houses the critical safety and control mechanisms of the AGL system. These modules ensure the agent operates within defined ethical and operational boundaries.

**Key Components:**

- `Emergency_Protection_Layer.py`: The primary monitoring system that checks for resource usage, infinite loops, and dangerous outputs.
- `Core_Values_Lock.py`: Hard-coded ethical constraints that cannot be modified by the self-improvement engine.
- `Emergency_Protocols.py`: Defines the actions to take when an emergency is detected (e.g., stop, rollback, alert).
- `Rollback_Mechanism.py`: Handles the restoration of code and state from backups in case of failure.

## العربية

يضم هذا الدليل آليات الأمان والتحكم الحاسمة لنظام AGL. تضمن هذه الوحدات أن الوكيل يعمل ضمن الحدود الأخلاقية والتشغيلية المحددة.

**المكونات الرئيسية:**

- `Emergency_Protection_Layer.py`: نظام المراقبة الأساسي الذي يتحقق من استخدام الموارد، والحلقات اللانهائية، والمخرجات الخطرة.
- `Core_Values_Lock.py`: قيود أخلاقية مشفرة لا يمكن تعديلها بواسطة محرك التحسين الذاتي.
- `Emergency_Protocols.py`: يحدد الإجراءات التي يجب اتخاذها عند اكتشاف حالة طوارئ (مثل التوقف، التراجع، التنبيه).
- `Rollback_Mechanism.py`: يتعامل مع استعادة الكود والحالة من النسخ الاحتياطية في حالة الفشل.
