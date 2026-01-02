import os
import shutil
import re

def cleanup_backups():
    root_dir = os.getcwd()
    backup_archive = os.path.join(root_dir, "backups", "archive")
    os.makedirs(backup_archive, exist_ok=True)
    
    # Pattern for timestamp folders (e.g., 1762911469338)
    timestamp_pattern = re.compile(r'^\d{13}$')
    
    moved_count = 0
    
    print(f"Scanning {root_dir} for timestamped backup folders...")
    
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        
        if os.path.isdir(item_path) and timestamp_pattern.match(item):
            target_path = os.path.join(backup_archive, item)
            print(f"Moving {item} to {target_path}...")
            try:
                shutil.move(item_path, target_path)
                moved_count += 1
            except Exception as e:
                print(f"Error moving {item}: {e}")
                
    print(f"Cleanup complete. Moved {moved_count} folders to {backup_archive}.")

if __name__ == "__main__":
    cleanup_backups()
