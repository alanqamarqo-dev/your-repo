# -*- coding: utf-8 -*-
import json
from datetime import datetime
import uuid
from typing import List


def extract_keywords(text: str):
    # استخراج كلمات مفتاحية بسيطة
    stop_words = {'في', 'من', 'على', 'إلى', 'و', 'أو', 'هي', 'كان', 'يكون'}
    words = text.split()
    return [word for word in words if len(word) > 3 and word not in stop_words][:10]


def create_enriched_events() -> List[dict]:
    events = []

    topics = {
        'نفط وطاقة': [
            "انخفاض أسعار النفط عام 2020 بسبب جائحة كورونا وتقلص الطلب العالمي",
            "أثر اتفاقيات أوبك+ على استقرار أسواق النفط الدولية",
            "التحول towards الطاقة المتجددة وتأثيره على مستقبل النفط",
            "تقلبات أسعار النفط الخام في الأسواق العالمية وأسبابها",
            "استثمارات الشركات النفطية في التقنيات الجديدة والاستكشاف"
        ],
        'تكنولوجيا وذكاء اصطناعي': [
            "تطور نماذج الذكاء الاصطناعي وتأثيرها على سوق العمل",
            "أحدث التقنيات في معالجة اللغات الطبيعية والفهم الآلي",
            "التعلم العميق وشبكات الذاكرة الطويلة المدى",
            "تطبيقات الرؤية الحاسوبية في المجال الطبي",
            "أمن المعلومات وحماية أنظمة الذكاء الاصطناعي"
        ],
        'اقتصاد وأسواق': [
            "تأثير التضخم على الاقتصادات العالمية وأسعار الفائدة",
            "أسواق الأسهم والعوامل المؤثرة على تقلباتها",
            "الاقتصاد الرقمي وتأثيره على النماذج التقليدية",
            "الاستثمار في العملات الرقمية والمخاطر المرتبطة بها",
            "السياسات النقدية للبنوك المركزية وأثرها على النمو"
        ],
        'صحة وطب': [
            "التطورات الحديثة في علاج الأمراض المزمنة",
            "تأثير جائحة COVID-19 على الأنظمة الصحية العالمية",
            "الطب الشخصي والعلاجات المستهدفة",
            "التقنيات الحديثة في التشخيص المبكر للأمراض",
            "الذكاء الاصطناعي في تحليل البيانات الطبية"
        ],
        'علوم وهندسة': [
            "أحدث التطورات في الحوسبة الكمية وتطبيقاتها",
            "هندسة المواد وتطوير مواد ذكية جديدة",
            "الاستدامة والطاقات المتجددة في العمران",
            "علوم الفضاء والبعثات الاستكشافية الجديدة",
            "التقنيات الحديثة في تحلية المياه"
        ]
    }

    for category, texts in topics.items():
        for i, text in enumerate(texts):
            event = {
                'id': str(uuid.uuid4()),
                'ts': datetime.now().timestamp(),
                'type': 'knowledge',
                'payload': {
                    'category': category,
                    'text': text,
                    'language': 'ar' if any('\u0600' <= c <= '\u06FF' for c in text) else 'en',
                    'keywords': extract_keywords(text),
                    'importance': 0.8
                },
                'trace_id': str(uuid.uuid4())
            }
            events.append(event)

    return events


def enrich_existing_memory() -> int:
    try:
        from Core_Memory.bridge_singleton import get_bridge
    except Exception:
        # try alternative path if package layout differs
        from Core_Memory.bridge_singleton import get_bridge

    bridge = get_bridge()

    new_events = create_enriched_events()

    for event in new_events:
        # use move-to-ltm style insertion
        bridge.ltm[event['id']] = event

    print(f"تم إضافة {len(new_events)} حدثًا غنيًا إلى الذاكرة")

    try:
        exported = bridge.export_ltm_to_db()
        print(f"تم تصدير {exported} حدث إلى قاعدة البيانات")
    except Exception as e:
        print('خطأ في تصدير القاعدة:', e)

    return len(new_events)


if __name__ == '__main__':
    enrich_existing_memory()


def create_massive_enriched_events(target_count: int = 2000) -> list:
    """Create a larger set of enriched events (target_count). Returns list of events."""
    import re
    from datetime import datetime
    events = []
    uuid_local = uuid

    expanded_topics = {
        'نفط وطاقة': [
            "أسعار النفط تنخفض بشكل حاد في 2020 بسبب جائحة كورونا وانخفاض الطلب العالمي",
            "أوبك+ تتفق على خفض الإنتاج لتحقيق استقرار أسواق النفط الدولية",
            "التحول towards الطاقة المتجددة يهدد مستقبل صناعة النفط التقليدية",
            "التقلبات في أسعار النفط الخام تؤثر على الاقتصادات العالمية",
            "الاستثمار في التقنيات النفطية الجديدة واستكشاف الحقول",
            "أثر العقوبات الدولية على صادرات النفط في بعض الدول",
            "مستقبل النفط في ظل التحول towards الطاقة النظيفة",
            "تأثير التغيرات المناخية على صناعة النفط والغاز"
        ],
        'ذكاء اصطناعي وتكنولوجيا': [
            "تطور نماذج الذكاء الاصطناعي الكبيرة وتطبيقاتها في الصناعة",
            "التعلم العميق يحقق تقدمًا في معالجة الصور واللغة",
            "الشبكات العصبية تتفوق في مهام الرؤية الحاسوبية",
            "التعلم المعزز يستخدم في الألعاب والروبوتات وتحسين العمليات",
            "معالجة اللغات الطبيعية تحسن فهم النصوص والترجمة الآلية",
            "الذكاء الاصطناعي في التشخيص الطبي وتحليل البيانات الصحية",
            "أمن الذكاء الاصطناعي ومخاطر الهجمات على النماذج",
            "أخلاقيات وتنظيم تطبيقات الذكاء الاصطناعي"
        ],
        'اقتصاد وأسواق': [
            "تأثير التضخم على الاقتصادات العالمية وأسعار الفائدة",
            "أسواق الأسهم والعوامل المؤثرة على تقلباتها",
            "الاقتصاد الرقمي وتأثيره على النماذج التقليدية",
            "الاستثمار في العملات الرقمية والمخاطر المرتبطة بها",
            "السياسات النقدية للبنوك المركزية وأثرها على النمو"
        ],
        'صحة وطب': [
            "التطورات الحديثة في علاج الأمراض المزمنة",
            "تأثير جائحة COVID-19 على الأنظمة الصحية العالمية",
            "الطب الشخصي والعلاجات المستهدفة",
            "التقنيات الحديثة في التشخيص المبكر للأمراض",
            "الذكاء الاصطناعي في تحليل البيانات الطبية"
        ],
        'علوم وهندسة': [
            "أحدث التطورات في الحوسبة الكمية وتطبيقاتها",
            "هندسة المواد وتطوير مواد ذكية جديدة",
            "الاستدامة والطاقات المتجددة في العمران",
            "علوم الفضاء والبعثات الاستكشافية الجديدة",
            "التقنيات الحديثة في تحلية المياه"
        ]
    }

    # helper: simple arabic keyword extractor
    def _extract_arabic_keywords(text: str):
        words = re.findall(r'[\u0600-\u06FF]{3,}', text)
        stop = {'في', 'من', 'على', 'إلى', 'أن', 'إن', 'كان', 'هذا', 'هذه'}
        return [w for w in words if w not in stop][:8]

    # generate events
    for category, texts in expanded_topics.items():
        i = 0
        while len(events) < target_count:
            base_text = texts[i % len(texts)]
            varied_text = f"{base_text} - النقاش {i+1} في مجال {category}"
            event = {
                'id': str(uuid_local.uuid4()),
                'ts': datetime.now().timestamp() + i,
                'type': 'knowledge',
                'payload': {
                    'category': category,
                    'text': varied_text,
                    'language': 'ar',
                    'keywords': _extract_arabic_keywords(varied_text),
                    'importance': 0.7 + ((i % 10) * 0.01)
                },
                'trace_id': str(uuid_local.uuid4())
            }
            events.append(event)
            i += 1
            # break if reached target
            if len(events) >= target_count:
                break

    return events


def create_comprehensive_events(target_count: int = 5000):
    """Create a comprehensive set of enriched events covering many domains.

    This generates a roughly balanced distribution across topics described
    by the user plan and returns up to `target_count` events.
    """
    from datetime import datetime
    import re

    topic_distribution = {
        'نفط وطاقة': 800,
        'ذكاء اصطناعي وتكنولوجيا': 800,
        'اقتصاد وأسواق': 800,
        'صحة وطب': 800,
        'علوم وهندسة': 800,
        'تعليم وبحث': 500,
        'بيئة واستدامة': 500
    }

    def generate_diverse_content(category: str, i: int) -> str:
        base = f"نقاش {i+1} حول {category}"
        extras = [
            "التحديات الراهنة والاتجاهات المستقبلية",
            "أحدث الأبحاث والتطبيقات العملية",
            "التأثير الاقتصادي والاجتماعي",
            "دور التكنولوجيا في التطوير والابتكار",
            "سياسات واستراتيجيات القطاع"
        ]
        return f"{base} - {extras[i % len(extras)]}"

    events = []
    uuid_local = uuid
    for category, count in topic_distribution.items():
        for i in range(count):
            text = generate_diverse_content(category, i)
            event = {
                'id': str(uuid_local.uuid4()),
                'ts': datetime.now().timestamp() + i,
                'type': 'knowledge',
                'payload': {
                    'category': category,
                    'text': text,
                    'language': 'ar' if any('\u0600' <= c <= '\u06FF' for c in text) else 'en',
                    'keywords': extract_keywords(text),
                    'importance': 0.7
                },
                'trace_id': str(uuid_local.uuid4())
            }
            events.append(event)
            if len(events) >= target_count:
                break
        if len(events) >= target_count:
            break

    return events[:target_count]
