"""
Script to clean up backup files by moving them to a backup directory.
"""
import os
import shutil
from datetime import datetime

def create_backup_dir():
    """Create a backup directory with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(__file__), f"old_backups_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def should_move_file(file_path):
    """Check if file should be moved to backup."""
    # Don't move files from venv
    if "venv" in file_path:
        return False
        
    # Don't move non-backup files
    if not any(file_path.endswith(ext) for ext in ['.bak', '.old', '.backup', '~']):
        return False
        
    return True

def move_backup_files():
    """Move backup files to a timestamped backup directory."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    backup_dir = create_backup_dir()
    
    moved_files = []
    
    for root, _, files in os.walk(project_root):
        for file in files:
            file_path = os.path.join(root, file)
            if should_move_file(file_path):
                # Create relative path structure in backup dir
                rel_path = os.path.relpath(root, project_root)
                backup_subdir = os.path.join(backup_dir, rel_path)
                os.makedirs(backup_subdir, exist_ok=True)
                
                # Move file
                backup_path = os.path.join(backup_subdir, file)
                shutil.move(file_path, backup_path)
                moved_files.append(os.path.relpath(file_path, project_root))
    
    return backup_dir, moved_files

if __name__ == "__main__":
    backup_dir, moved_files = move_backup_files()
    
    if moved_files:
        print(f"\nMoved {len(moved_files)} backup files to: {backup_dir}")
        print("\nMoved files:")
        for file in moved_files:
            print(f"  - {file}")
    else:
        print("No backup files found to move.")
