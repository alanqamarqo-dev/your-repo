import sys
import os

file_path = r"D:\AGL\repo-copy\Learning_System\Feedback_Analyzer.py"

print(f"--- Inspecting: {file_path} ---")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        found = False
        for line in lines:
            if line.strip().startswith("class ") or line.strip().startswith("def "):
                print(f"FOUND: {line.strip()}")
                found = True
        if not found:
            print("⚠️ File appears empty or has no classes/functions defined.")
except Exception as e:
    print(f"Error reading file: {e}")
