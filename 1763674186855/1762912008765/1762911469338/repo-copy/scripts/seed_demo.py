"""Seed demo LTM documents for local testing (8 topics x 6 samples = 48 records).

Usage:
  py -3 scripts/seed_demo.py

This uses the ConsciousBridge `put` API so events have the expected shape
and are exported to the repo `data/memory_seeded.sqlite` file. After running
copy the seeded DB to the default path or set AGL_ARTIFACTS_DIR.
"""
import sys, time, os
sys.path.insert(0, r'D:\AGL\repo-copy')
from Core_Memory.bridge_singleton import get_bridge

def seed(topic, base, kws, n=6):
    b = get_bridge()
    for i in range(n):
        txt = f"{base} — {kws} — عينة {i}"
        b.put("seed_doc", {"topic": topic, "text": txt, "ts": time.time()}, to="ltm")

def main():
    b = get_bridge()
    # clear in-memory to avoid duplicates when re-running interactively
    b.ltm.clear()

    seed("نفط وطاقة", "انخفضت أسعار النفط عام 2020 بسبب الجائحة والطلب العالمي", "نفط أسعار 2020")
    seed("ذكاء اصطناعي", "يتقدم الذكاء الاصطناعي وتعلم الآلة في التطبيقات العملية", "ذكاء اصطناعي تعلم آلة")
    seed("اقتصاد وأسواق", "ارتفع التضخم في الأسواق الناشئة وأثّر على سلوك المستهلك", "اقتصاد تضخم أسواق")
    seed("صحة وطب", "أحدثت جائحة كوفيد تغيّرات كبيرة في أنظمة الصحة العامة", "صحة جائحة كوفيد")
    seed("طاقة متجددة", "التحول إلى الطاقة المتجددة ضرورة للاستدامة وخفض الانبعاثات", "طاقة متجددة مستدامة")
    seed("بلوك تشين", "تقنية البلوك تشين توفّر سجلات موزعة شفافة وآمنة", "تكنولوجيا بلوك تشين")
    seed("أمراض مزمنة", "إدارة الأمراض المزمنة تتطلب رعاية مستمرة وخطط علاجية", "طب أمراض مزمنة")
    seed("مواد ذكية", "الهندسة المتقدمة تطوّر مواد ذكية بخصائص استجابية", "هندسة مواد ذكية")

    print("LTM_size =", len(b.ltm))
    written = b.export_ltm_to_db()
    print("exported =", written)
    reidx = b.build_semantic_index()
    print("reindex  =", reidx)

    # copy to default file for convenience (this is a no-op if export used default path)
    try:
        src = os.path.join(os.path.dirname(__file__), '..', 'data', 'memory_seeded.sqlite')
        # best-effort: if a default memory file exists, leave it for the user to decide
    except Exception:
        pass

if __name__ == '__main__':
    main()
