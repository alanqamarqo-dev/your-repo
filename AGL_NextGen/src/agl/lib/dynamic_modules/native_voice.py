import os


def speak(text):
    # Explicitly call PowerShell so Add-Type is recognized
    command = (
        "powershell -Command \"Add-Type -AssemblyName System.Speech; "
        "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('" + text.replace('"', '\\"') + "')\""
    )
    os.system(command)


if __name__ == "__main__":
    speak("Hello, this is a test.")
