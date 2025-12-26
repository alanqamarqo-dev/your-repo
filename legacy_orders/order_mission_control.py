import argparse
import requests
import json

url = "http://127.0.0.1:8000/chat"

# نطلب منه بناء "مدير" يفكك الطلبات المعقدة
prompt = (
    "STRICT: Write a Python module named 'mission_control'. "
    "This tool orchestrates complex tasks using available engines. "
    "1. Create a function 'execute_mission(complex_prompt)'. "
    "2. Inside, use 'requests.post' to call the chat API (localhost:8000) with a system prompt: "
    "'You are a Planner. Break down the user request into a JSON list of steps. "
    "Format: [{\"engine\": \"EngineName\", \"task\": \"Specific Instruction\"}]. "
    "Available Engines: PhysicsSolver, ChemistrySolver, CodeGenerator, EmergencyDoctor'. "
    "3. Parse the returned JSON list. "
    "4. Loop through each step, calling the API again for that specific engine/task. "
    "5. Aggregate results into a final report string. "
    "6. Print the Final Mission Report."
)


def main(execute: bool = False) -> None:
    """If `execute` is True, send the prompt to the local chat API.

    By default the script is safe: it only prints the prompt and exits.
    This prevents accidental automatic code generation that can create
    self-calling modules or loops. Use `--execute` to opt-in.
    """
    print("🚀 Ordering Mission Control Center...")
    print("\n--- Prompt (preview) ---\n")
    print(prompt)

    if not execute:
        print("\nScript is in SAFE mode. To actually POST to the server, re-run with --execute")
        return

    payload = {"message": prompt}

    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            print("\n✅ Code Generated:\n")
            print(response.json().get("reply", ""))
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Order Mission Control (safe by default)')
    parser.add_argument('--execute', action='store_true', help='Actually POST the prompt to the local chat API')
    args = parser.parse_args()
    main(execute=args.execute)