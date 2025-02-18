"""
Command-line tool to analyze code changes
"""

import os
import argparse
from app.utils.diff_analyzer import DiffAnalyzer

def analyze_file_changes(file_path: str, backup_path: str = None):
    """
    Analyze changes between current file and its backup.
    """
    # If no backup path provided, use .bak extension
    if not backup_path:
        backup_path = f"{file_path}.bak"
    
    # Read current and backup content
    try:
        with open(file_path, 'r') as f:
            current_content = f.read()
            
        with open(backup_path, 'r') as f:
            backup_content = f.read()
    except FileNotFoundError as e:
        print(f"Error: Could not find file - {str(e)}")
        return
        
    # Analyze changes
    analyzer = DiffAnalyzer()
    changes = analyzer.analyze_changes(backup_content, current_content)
    
    # Print report
    print(f"\nAnalyzing changes in {os.path.basename(file_path)}:")
    print("=" * 80)
    print(analyzer.format_report(changes))

def main():
    parser = argparse.ArgumentParser(description='Analyze code changes between files')
    parser.add_argument('file', help='Path to the current file')
    parser.add_argument('--backup', help='Path to the backup file (optional)')
    
    args = parser.parse_args()
    analyze_file_changes(args.file, args.backup)

if __name__ == "__main__":
    main()
