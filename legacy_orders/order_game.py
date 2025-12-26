import requests
import json

# رابط السيرفر
url = "http://127.0.0.1:8000/chat"

# الأمر الصارم (لاحظ التفاصيل المطلوبة)
prompt = (
    "STRICT: Write a Python module named 'snake_game'. "
    "Use 'tkinter' library to create a classic Snake Game. "
    "Requirements:\n"
    "1. Use a Canvas widget for rendering.\n"
    "2. Control snake with Arrow Keys (Up, Down, Left, Right).\n"
    "3. Snake grows when it eats food.\n"
    "4. Game Over if snake hits wall or itself.\n"
    "5. Include 'if __name__ == \"__main__\":' block to run it immediately."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Snake Game from Genesis Core...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("\n✅ Server Response (Code Generated):")
        print("The AI has written the game code. Check 'dynamic_modules/snake_game.py'")
    else:
        print(f"❌ Error: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")
