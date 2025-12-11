import os
import shutil
import datetime

def create_restore_point():
    # Define source and destination
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir_name = f"backup_restore_point_{timestamp}"
    backup_path = os.path.join(root_dir, "backups", backup_dir_name)
    
    # Create backups directory if it doesn't exist
    if not os.path.exists(os.path.join(root_dir, "backups")):
        os.makedirs(os.path.join(root_dir, "backups"))
        
    print(f"Creating restore point at: {backup_path}")
    
    # Directories to backup
    dirs_to_backup = [
        "repo-copy",
        "artifacts",
        "dynamic_modules" # If it exists in root
    ]
    
    # Files to backup
    files_to_backup = [
        "SCIENTIFIC_SYSTEM_DOCS.md"
    ]
    
    os.makedirs(backup_path)
    
    for dir_name in dirs_to_backup:
        src = os.path.join(root_dir, dir_name)
        dst = os.path.join(backup_path, dir_name)
        if os.path.exists(src):
            print(f"Backing up directory: {dir_name}")
            shutil.copytree(src, dst)
        else:
            print(f"Skipping directory (not found): {dir_name}")

    for file_name in files_to_backup:
        src = os.path.join(root_dir, file_name)
        dst = os.path.join(backup_path, file_name)
        if os.path.exists(src):
            print(f"Backing up file: {file_name}")
            shutil.copy2(src, dst)
        else:
            print(f"Skipping file (not found): {file_name}")
            
    print(f"Restore point created successfully: {backup_dir_name}")

if __name__ == "__main__":
    create_restore_point()
