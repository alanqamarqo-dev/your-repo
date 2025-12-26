import requests
import json

url = "http://127.0.0.1:8000/chat"

# نطلب استخدام PowerShell بدلاً من pyautogui
prompt = (
    "STRICT: Write a Python module named 'native_screen_eye'. "
    "Do NOT use external libraries like 'pyautogui' or 'PIL'. "
    "Instead, use 'subprocess' to run a PowerShell command that takes a screenshot. "
    "The PowerShell command is: "
    "[Reflection.Assembly]::LoadWithPartialName('System.Drawing'); "
    "$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
    "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
    "$graphics.CopyFromScreen(0, 0, 0, 0, $bmp.Size); "
    "$bmp.Save('vision_capture.png');"
    "Run this command and print 'Screenshot captured successfully via Native PowerShell'."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Native Vision Tool...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
