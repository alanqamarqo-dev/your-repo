import os

def scan_structure():
    core_engines = []
    dynamic_modules = []
    scripts = []

    for root, dirs, files in os.walk('.'):
        if any(part in root for part in ['__pycache__', '.git']):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            if 'Core_Engines' in full_path:
                core_engines.append(full_path)
            elif 'dynamic_modules' in full_path:
                dynamic_modules.append(full_path)
            else:
                scripts.append(full_path)

    return {'Core_Engines': core_engines, 'dynamic_modules': dynamic_modules, 'scripts': scripts}

if __name__ == "__main__":
    structure = scan_structure()
    print("Project Structure:")
    for key, value in structure.items():
        print(f"{key}:")
        for file in value:
            print(f"  - {file}")
