import requests
import sys
import os

# إضافة مجلد الوحدات الديناميكية للمسار لاستخدام الصوت
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'repo-copy', 'dynamic_modules'))
sys.path.append(base_dir)

try:
    import native_voice # استيراد الأداة التي صنعها النظام
except ImportError:
    print("❌ Voice module not found! Run order_native_voice.py first.")
    sys.exit()

SERVER_URL = "http://127.0.0.1:8000/chat"

def chat_loop():
    print("🎙️ AGL Voice Interface Online. Type 'exit' to quit.\n")
    native_voice.speak("System Online. I am listening.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            native_voice.speak("Shutting down. Goodbye.")
            break
            
        try:
            # 1. إرسال السؤال للسيرفر
            print("Thinking...")
            response = requests.post(SERVER_URL, json={"message": user_input})
            
            if response.status_code == 200:
                reply = response.json().get("reply", "")
                
                # تنظيف الرد من الرموز البرمجية لكي يكون القراءة واضحة
                clean_reply = reply.replace("*", "").replace("`", "").split("\n")[0] # يقرأ السطر الأول فقط
                
                print(f"AGL: {reply}")
                
                # 2. النطق بالرد
                native_voice.speak(clean_reply)
            else:
                print("Error from server.")
                
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    chat_loop()
