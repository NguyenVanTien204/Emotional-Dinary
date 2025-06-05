import os
import subprocess
from pathlib import Path

def restore_backup(backup_path=None):
    backup_dir = Path("backups")
    
    if not backup_path:
        # Nếu không chỉ định backup cụ thể, sử dụng bản mới nhất
        backup_files = sorted(backup_dir.glob("emotional_diary_backup_*"))
        if not backup_files:
            print("No backup files found!")
            return
        backup_path = backup_files[-1]
    
    try:
        # Thực hiện restore với mongorestore
        subprocess.run([
            "mongorestore",
            "--uri=mongodb://localhost:27017/emotional_diary_db",
            f"--dir={backup_path}",
            "--drop",  # Xóa collections hiện tại trước khi restore
            "--gzip"
        ], check=True)
        print(f"Restore completed successfully from {backup_path}")
    
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import sys
    backup_path = sys.argv[1] if len(sys.argv) > 1 else None
    restore_backup(backup_path)
