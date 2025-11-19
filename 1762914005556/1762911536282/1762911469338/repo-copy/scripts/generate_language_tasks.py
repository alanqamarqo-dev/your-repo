#!/usr/bin/env python3
"""Generate 10 language-training CSV files (Arabic-focused) for the learning system.

Each CSV has fields: prompt, expected
Tasks include: paraphrase, synonym, antonym, translation (en->ar), sentence completion,
grammar correction, sentiment, summarization, question generation, NER.
"""
import os, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'training' / 'language_tasks'
OUT.mkdir(parents=True, exist_ok=True)

TASKS = [
    ('paraphrase', [
        ("أعد صياغة الجملة التالية بأسلوب أبسط: 'الطقس اليوم مُتقلب'", "الجو متغير اليوم"),
        ("أعد الصياغة: 'وصلت الرسالة في موعدها'", "الرسالة وصلت في وقتها")
    ]),
    ('synonym', [
        ("مرادف كلمة 'سريع'", "عاجل"),
        ("مرادف كلمة 'سعيد'", "مسرور")
    ]),
    ('antonym', [
        ("عكس كلمة 'قوي'", "ضعيف"),
        ("عكس كلمة 'بارد'", "حار")
    ]),
    ('translate_en_to_ar', [
        ("Translate to Arabic: 'The rover landed on the moon'", "هبط المسبار على القمر"),
        ("Translate to Arabic: 'Water freezes at 0 degrees Celsius'", "الماء يتجمد عند صفر درجة مئوية")
    ]),
    ('complete_sentence', [
        ("أكمل الجملة: 'ذهب محمد إلى السوق لِـ'", "شراء الخبز"),
        ("أكمل: 'أَحمد يدرس بجد كي يصبح'", "مهندسًا ناجحًا")
    ]),
    ('grammar_fix', [
        ("صحح النحو: 'هو ذهبو الى المدرسة'", "هو ذهب إلى المدرسة"),
        ("صحح: 'انا قرأت الكتابا'", "أنا قرأت الكتاب")
    ]),
    ('sentiment', [
        ("ما شعور الجملة: 'أنا أحب العطلات'", "إيجابي"),
        ("ما شعور: 'هذا سيء جدًا'", "سلبي")
    ]),
    ('summarize', [
        ("اختر ملخصًا موجزًا: 'ذهب الفريق إلى اللقاء، تناقشوا في الخطة، وتم اتخاذ قرار.'", "الاجتماع حسم الخطة واتُّخذ قرار"),
        ("لخص: 'نشاطات اليوم شملت تدريبًا ومحاضرة'", "شملت اليوم تدريبًا ومحاضرة")
    ]),
    ('question_gen', [
        ("اصنع سؤالًا عن الجملة: 'سافر خالد إلى باريس في الصيف'", "أين سافر خالد؟"),
        ("من هو الذي سافر؟ عن: 'سافر سامي إلى اليابان'", "من سافر إلى اليابان؟")
    ]),
    ('ner', [
        ("استخرج الكيانات: 'زار الرئيس الأكراد اليوم'", "الرئيس; الأكراد"),
        ("كيانات: 'شركة أبل أصدرت منتجًا جديدًا'", "شركة أبل")
    ])
]

def write_task(kind, pairs):
    path = OUT / f'lang_task_{kind}.csv'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['prompt','expected'])
        w.writeheader()
        for p,e in pairs:
            w.writerow({'prompt': p, 'expected': e})
    print('Wrote', path)

def main():
    for kind, pairs in TASKS:
        write_task(kind, pairs)
    print('Generated language tasks under', OUT)

if __name__ == '__main__':
    main()
