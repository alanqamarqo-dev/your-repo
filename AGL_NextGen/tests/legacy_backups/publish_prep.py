import os
import re

# Configuration
target_root_name = "AGL"
target_hardcoded_patterns = [
    r"['\"]d:\\AGL",
    r"['\"]D:\\AGL",
    r"['\"]d:/AGL",
    r"['\"]D:/AGL"
]

def get_dynamic_path_code(file_path, root_dir):
    """
    Calculates the relative path from the file to the root directory
    and returns a Python code snippet to reconstruct it.
    """
    try:
        rel_path = os.path.relpath(root_dir, os.path.dirname(file_path))
    except ValueError:
        return None

    path_parts = rel_path.split(os.sep)
    
    # Construct os.path.join(os.path.dirname(__file__), '..', '..')
    joins = ", ".join([f"'{p}'" for p in path_parts])
    
    # If same directory
    if rel_path == ".":
        return "os.path.dirname(os.path.abspath(__file__))"
    
    return f"os.path.abspath(os.path.join(os.path.dirname(__file__), {joins}))"

def process_file(file_path, root_dir):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip binary files

    original_content = content
    modified = False
    
    # Check for hardcoded paths
    for pattern in target_hardcoded_patterns:
        # We look for the pattern followed by optional path components
        # matches: "D:\AGL" or "D:\AGL\src"
        
        # Regex to find string literals starting with the hardcoded path
        # Group 1: Quote char
        # Group 2: The hardcoded root
        # Group 3: The rest of the path inside the string
        regex = re.compile(r"([rf]?['\"])" + pattern[4:] + r"([^'\"]*)(['\"])", re.IGNORECASE)
        
        candidates = list(regex.finditer(content))
        
        if not candidates:
            continue

        # We need "os" module if we are going to use os.path
        if "import os" not in content and candidates:
             content = "import os\n" + content
             # Re-index candidates not needed if we just prepend, but offsets shift. 
             # Simpler to just proceed and rely on replace logic string-by-string? 
             # No, better active content updates.
             
        # Reverse iterate to replace without messing up indices
        for match in reversed(candidates):
            full_match = match.group(0)
            quote_start = match.group(1)
            rest_of_path = match.group(2) # e.g. \src\agl
            quote_end = match.group(3)
            
            # Normalize rest_of_path to forward slashes for joining or keep raw?
            # If we replacing "D:\AGL\src" with os.path.join(ROOT, "src")
            
            dynamic_root_code = get_dynamic_path_code(file_path, root_dir)
            
            if not dynamic_root_code:
                continue

            # Check if it is a simple path or has subdirs
            if not rest_of_path:
                # "D:\AGL" -> dynamic_root_code
                replacement = dynamic_root_code
            else:
                # "D:\AGL\src" -> os.path.join(dynamic_root_code, "src")
                # Clean up slash
                clean_rest = rest_of_path.lstrip('\\/').replace('\\', '/')
                replacement = f"os.path.join({dynamic_root_code}, '{clean_rest}')"
            
            print(f"   [FIX] {file_path}: Replaced {full_match} -> Dynamic Path")
            
            # Perform replacement in content string (taking care of the specific instance)
            # Find the match span and replace
            start, end = match.span()
            # We must adjust for the initial import added if any
            if "import os" not in original_content and "import os" in content:
                 offset = len("import os\n")
                 start += offset
                 end += offset
            
            content = content[:start] + replacement + content[end:]
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"🚀 Starting Publication Preparation Scan in: {root_dir}")
    print("---------------------------------------------------")
    
    count = 0
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden/env dirs
        if ".venv" in root or "node_modules" in root or ".git" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file == "publish_prep.py": continue
            
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if process_file(file_path, root_dir):
                    count += 1
    
    print("---------------------------------------------------")
    print(f"✅ CLEANUP COMPLETE. Fixed {count} files.")
    print("   The project is now more portable.")

if __name__ == "__main__":
    main()
