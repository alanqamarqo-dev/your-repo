try:
    import pyttsx3 # type: ignore
except ImportError:
    pyttsx3 = None


def speak(text):
    if not pyttsx3:
        print(f"[voice_engine] pyttsx3 missing, skipping speech for: {text}")
        return None

    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

if __name__ == "__main__":
    speak("Hello, I am AGL Genesis Beta. I can speak now.")
