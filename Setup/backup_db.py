import os
import datetime
import subprocess
from pathlib import Path

def create_backup():
    # Tạo thư mục backup nếu chưa tồn tại
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Tạo tên file backup với timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"emotional_diary_backup_{timestamp}"
    
    try:
        # Thực hiện backup với mongodump
        subprocess.run([
            "mongodump",
            "--uri=mongodb://localhost:27017/emotional_diary_db",
            f"--out={backup_file}",
            "--gzip"
        ], check=True)
        print(f"Backup created successfully at {backup_file}")
        
        # Xóa các backup cũ (giữ lại 5 bản gần nhất)
        backup_files = sorted(backup_dir.glob("emotional_diary_backup_*"))
        if len(backup_files) > 5:
            for old_backup in backup_files[:-5]:
                os.remove(old_backup)
                print(f"Removed old backup: {old_backup}")
    
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_backup()
