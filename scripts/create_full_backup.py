import os
import shutil
import datetime

def create_backup():
    # Setup paths
    source_dir = r"d:\AGL"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(source_dir, "backups", f"backup_{timestamp}_FINAL")
    
    # Ignore patterns
    ignore_patterns = shutil.ignore_patterns(
        ".venv", "__pycache__", ".git", "node_modules", 
        "*.pyc", "*.log", "tmp_*", "backups", "coverage_html", "htmlcov"
    )
    
    print(f"📦 Starting backup to: {backup_dir}")
    
    try:
        shutil.copytree(source_dir, backup_dir, ignore=ignore_patterns)
        print(f"✅ Backup completed successfully!")
        print(f"📂 Location: {backup_dir}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    create_backup()
