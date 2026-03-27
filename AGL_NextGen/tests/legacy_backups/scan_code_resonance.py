import os
import re
import sys
import argparse

# ==========================================
# ⚙️ AGL RESONANCE SCANNER - FIRMWARE EDITION
# ==========================================

# 1. Resonance Patterns (Vulnerability Signatures)
RESONANCE_PATTERNS = {
    "MEMORY_LEAK": [
        (r"strcpy\(", "Unsafe string copy (Buffer Overflow Risk)"),
        (r"memcpy\(", "Unsafe memory copy (Buffer Overflow Risk)"),
        (r"sprintf\(", "Unsafe formatting (Buffer Overflow Risk)"),
        (r"gets\(", "Extremely unsafe input (Stack Smash Risk)")
    ],
    "WEAK_CRYPTO": [
        (r"rand\(", "Weak PRNG (Predictable)"),
        (r"srand\(", "Weak Seeding"),
        (r"MD5", "Broken Hash Algorithm"),
        (r"SHA1", "Deprecated Hash Algorithm")
    ],
    "SECRETS": [
        (r"private_key", "Potential Hardcoded Key"),
        (r"secret", "Potential Hardcoded Secret"),
        (r"password", "Potential Hardcoded Password"),
        (r"auth_token", "Potential Hardcoded Token")
    ]
}

def check_weak_randomness(content, filename):
    """
    Advanced Heuristic: Detects potential Nonce Reuse or Weak RNG usage.
    Focuses on variables often used for nonces (k, nonce, r) being assigned static values or weak RNG.
    """
    findings = []
    lines = content.split('\n')
    
    # Regex for assignment to common nonce variables
    # e.g., k = ..., nonce = ...
    nonce_vars = r"\b(k|nonce|r|s)\s*=\s*(.*);"
    
    for i, line in enumerate(lines):
        match = re.search(nonce_vars, line)
        if match:
            var_name = match.group(1)
            assignment = match.group(2).strip()
            
            # Check 1: Static assignment (e.g., k = 0; or k = FIXED_VAL;)
            if re.match(r"^[\d]+$", assignment) or re.match(r"^[A-Z_]+$", assignment):
                findings.append(f"⚠️ [CRITICAL] Potential Static Nonce: '{var_name}' assigned static value '{assignment}' at line {i+1}")
            
            # Check 2: Weak RNG assignment
            if "rand()" in assignment:
                findings.append(f"⚠️ [CRITICAL] Weak RNG for Nonce: '{var_name}' assigned via rand() at line {i+1}")

    return findings

def scan_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 1. Standard Pattern Scan
        for category, patterns in RESONANCE_PATTERNS.items():
            for pattern, desc in patterns:
                matches = list(re.finditer(pattern, content))
                for m in matches:
                    # Get line number
                    line_no = content[:m.start()].count('\n') + 1
                    findings.append(f"[{category}] {desc}: '{m.group()}' at line {line_no}")

        # 2. Advanced Weak Randomness Scan (C/C++ files only)
        if filepath.endswith(('.c', '.h', '.cpp')):
            rng_findings = check_weak_randomness(content, filepath)
            findings.extend(rng_findings)

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return findings

def main():
    parser = argparse.ArgumentParser(description="AGL Resonance Scanner")
    parser.add_argument("--target", required=True, help="Target directory to scan")
    args = parser.parse_args()
    
    target_dir = args.target
    print(f"🦅 [AGL] Scanning Target: {target_dir}")
    print("==================================================")
    
    total_files = 0
    dissonance_count = 0
    
    for root, dirs, files in os.walk(target_dir):
        # Exclude test and mock directories/files
        if 'test' in root.lower() or 'mock' in root.lower():
            continue

        for file in files:
            # Focus on source code
            if file.endswith(('.c', '.h', '.cpp', '.py', '.js', '.rs')):
                if 'test' in file.lower() or 'mock' in file.lower():
                    continue

                total_files += 1
                filepath = os.path.join(root, file)
                results = scan_file(filepath)
                
                if results:
                    dissonance_count += len(results)
                    rel_path = os.path.relpath(filepath, target_dir)
                    print(f"\n📂 {rel_path}")
                    for res in results:
                        if "CRITICAL" in res:
                            print(f"    🔴 {res}")
                        else:
                            print(f"    🔸 {res}")

    print("\n==================================================")
    print(f"📊 Scan Complete.")
    print(f"   Files Scanned: {total_files}")
    print(f"   Dissonance Events (Risks): {dissonance_count}")
    
    if dissonance_count > 0:
        print("\n🦅 AGL Insight: High Dissonance Detected. Potential Bounty Targets Identified.")
    else:
        print("\n✅ System Clean. No obvious resonance patterns found.")

if __name__ == "__main__":
    main()
