import requests
import urllib.parse
import os

class ImageAdapter:
    def __init__(self):
        # خدمة مجانية وسريعة جداً لتوليد الصور
        self.base_url = "https://image.pollinations.ai/prompt/"

    def generate_image(self, prompt: str) -> dict:
        """
        تقوم بتوليد رابط صورة بناءً على الوصف النصي.
        """
        try:
            # دالة تصحيحية صغيرة تطبع النص كما وصله للرسّام
            print(f"DEBUG: ماذا وصل للرسام: {prompt!r}")
            print(f"🎨 ImageAdapter: جاري رسم... '{prompt[:50]}...'")

            # 1. تحسين الوصف (اختياري): إضافة كلمات مفتاحية للجودة
            # ندمج الوصف مع كلمات تجعل الصورة احترافية
            enhanced_prompt = f"{prompt}, high quality, realistic, 4k, detailed"
            
            # 2. تشفير النص ليصبح صالحاً كـ رابط
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            
            # 3. تكوين الرابط النهائي
            # width/height: أبعاد الصورة
            # nologo: لإخفاء شعار الموقع
            final_url = f"{self.base_url}{encoded_prompt}?width=1024&height=768&nologo=true&seed=42"

            # 4. إرجاع النتيجة بتنسيق يفهمه السيرفر والواجهة
            # قبل الإرجاع، نمرر الصورة إلى "الناقد" (حالياً stub) للتحقق.
            # إذا فشل الناقد في التحقق، نحاول إعادة التوليد لعدد محدود من المحاولات.
            max_retries = 2
            attempt = 0
            while attempt <= max_retries:
                # عند المحاولة الأولى نستخدم final_url كما هو
                if attempt > 0:
                    # إعادة توليد: نغيّر البذرة (seed) لتحصل على نتيجة مختلفة
                    seed = 42 + attempt
                    final_url = f"{self.base_url}{encoded_prompt}?width=1024&height=768&nologo=true&seed={seed}"

                # فحص ناقد بسيط (حاليًا مجرد stub يطبع ويقبل دائماً)
                ok = self.verify_image_with_critic(final_url, prompt)
                if ok:
                    return {
                        "ok": True,
                        "type": "image",
                        "content": final_url,
                        "alt_text": prompt,
                        "text": f"![{prompt}]({final_url})"
                    }

                print(f"⚠️ ImageAdapter: الناقد رفض الصورة في المحاولة {attempt+1}. يعاد التوليد...")
                attempt += 1

            # إذا فشل كل شيء
            return {"ok": False, "error": "Image critic failed after retries"}
            
        except Exception as e:
            print(f"❌ Image Error: {e}")
            return {"ok": False, "error": str(e)}

    def verify_image_with_critic(self, image_url: str, prompt: str) -> bool:
        """
        Stub for a vision-model critic.
        حالياً الدالة تطبع ما فحصته وتُعيد True دائماً.

        مستقبلًا يُمكن استبدالها باستدعاء نموذج بصري يفحص محتوى الصورة
        ويُرجع True إذا كانت الصورة تطابق الوصف، أو False لتفعيل إعادة التوليد.
        """
        try:
            print(f"🔎 ImageAdapter.Critic: أتحقق من الصورة مقابل الوصف: {prompt!r}")
            # مثال مبسط: نتحقق ما إذا كانت كلمات مفتاحية من الوصف موجودة في رابط الـ prompt
            # (هذا لا يضمن مطابقة حقيقية — فقط مؤشر مبدئي).
            try:
                # نحاول استخراج الجزء المشفَّر من رابط pollinations
                if "/prompt/" in image_url:
                    encoded = image_url.split('/prompt/')[1].split('?')[0]
                    decoded = urllib.parse.unquote(encoded)
                else:
                    decoded = ""
            except Exception:
                decoded = ""

            print(f"🔎 ImageAdapter.Critic: prompt في الرابط (مشقوق): {decoded!r}")

            # حالياً نرجع True دائماً (قبول الصورة).
            return True
        except Exception as e:
            print(f"❌ Critic Error: {e}")
            return False

# --- اختبار سريع (Smoke Test) ---
if __name__ == "__main__":
    # عند تشغيل الملف مباشرة، يقوم بتجربة رسم صورة
    adapter = ImageAdapter()
    print("--- اختبار محرك الصور ---")
    result = adapter.generate_image("futuristic mars colony with glass domes")
    print("النتيجة:")
    print(result)
    print(f"\n✅ انسخ هذا الرابط في المتصفح لتراها:\n{result['content']}")
