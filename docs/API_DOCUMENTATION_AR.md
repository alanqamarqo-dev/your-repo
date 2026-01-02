# توثيق واجهة برمجة التطبيقات (API Documentation) - AGL Quantum Server

**الإصدار:** 2.0 (Quantum Enabled)
**الخادم:** `http://127.0.0.1:8000`

## نقاط النهاية الجديدة (Quantum Endpoints)

### 1. حالة النظام الكمومي

* **المسار:** `GET /quantum/status`
* **الوصف:** يعيد الحالة الحالية لمحركات الرنين، الإرادة، والوعي.
* **مثال الاستجابة:**

    ```json
    {
      "status": "active",
      "resonance_engine": "Online",
      "volition_engine": "Online",
      "consciousness_system": "Online",
      "timestamp": "2025-12-21T..."
    }
    ```

### 2. الإرادة الكمومية (Quantum Volition)

* **المسار:** `POST /quantum/volition`
* **الوصف:** يطلب من النظام اختيار هدف استراتيجي جديد. يستخدم النظام ميكانيكا الكم (النفق الكمومي) لاختيار أهداف ذات قيمة عالية حتى لو كانت صعبة التنفيذ.
* **جسم الطلب (Body):** فارغ (أو يمكن تخصيصه مستقبلاً).
* **مثال الاستجابة:**

    ```json
    {
      "status": "success",
      "goal": {
        "description": "Perform deep structural self-engineering...",
        "type": "structural_evolution",
        "_quantum_stats": {
          "importance": 0.95,
          "difficulty": 0.9,
          "tunnel_prob": 1.0
        }
      },
      "message": "Goal selected via Quantum Volition"
    }
    ```

### 3. الاستبصار الكمومي (Quantum Insight)

* **المسار:** `POST /quantum/insight`
* **الوصف:** يطلب من النظام دمج مجموعة من المدخلات لاستخراج "بصيرة" أو فهم عميق باستخدام نظرية المعلومات المتكاملة (IIT).
* **جسم الطلب (Body):**

    ```json
    {
      "inputs": [
        "الجملة الأولى للتحليل",
        "الجملة الثانية",
        "سياق إضافي"
      ]
    }
    ```

* **مثال الاستجابة:**

    ```json
    {
      "status": "success",
      "insight_achieved": false, // true if quantum boost > threshold
      "integration_result": {
        "phi": 0.0697,
        "synergy": 0.85,
        "unified_concept": "integrated_thought"
      }
    }
    ```

## ملاحظات هامة

* يجب التأكد من أن الخادم يعمل (`python repo-copy/server_fixed.py`) قبل استدعاء هذه النقاط.
* هذه النقاط تعتمد على تحميل المحركات الثقيلة (`VolitionEngine`, `ResonanceOptimizer`)، لذا قد تستغرق الاستجابة الأولى وقتاً أطول قليلاً.
