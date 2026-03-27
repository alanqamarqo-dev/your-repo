# Integration Layer / طبقة التكامل

## English

The glue that holds the system together. This layer manages the flow of information between engines and the core loop.

**Key Components:**

- `Action_Router.py`: Decides which engine should handle a given task.
- `Hybrid_Composer.py`: Constructs prompts by combining context, history, and instructions.
- `Global_Context.py`: Maintains the shared state accessible to all engines.

## العربية

الغراء الذي يربط النظام ببعضه البعض. تدير هذه الطبقة تدفق المعلومات بين المحركات والحلقة الأساسية.

**المكونات الرئيسية:**

- `Action_Router.py`: يقرر أي محرك يجب أن يتعامل مع مهمة معينة.
- `Hybrid_Composer.py`: يبني المطالبات من خلال الجمع بين السياق والتاريخ والتعليمات.
- `Global_Context.py`: يحافظ على الحالة المشتركة التي يمكن لجميع المحركات الوصول إليها.
