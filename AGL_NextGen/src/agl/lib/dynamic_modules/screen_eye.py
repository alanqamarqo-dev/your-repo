try:
    import pyautogui # type: ignore
except ImportError:
    pyautogui = None

from datetime import datetime


def capture_screenshot():
    if not pyautogui:
        print("Screen capture disabled: pyautogui is not available.")
        return None

    screenshot = pyautogui.screenshot()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"current_view_{timestamp}.png" if timestamp else "current_view.png"
    screenshot.save(filename)
    print("I can see your screen now.")
    return filename


if __name__ == "__main__":
    capture_screenshot()
