#!/usr/bin/env python3

import os
import time
import datetime
from pathlib import Path

def should_delete_file(file_path, now):
    """
    Determine if a file should be deleted based on age and creation date rules.
    
    Args:
        file_path: Path to the file
        now: Current datetime object
    
    Returns:
        True if file should be deleted, False otherwise
    """
    # Get file stats
    stat = file_path.stat()
    
    # Get file creation/modification time (use modification time as fallback)
    # On Linux, st_ctime is change time, not creation time. Using st_mtime for modification time
    file_time = stat.st_mtime
    
    # Convert to datetime
    file_date = datetime.datetime.fromtimestamp(file_time)
    
    # Calculate age
    age = now - file_date
    
    # Rule 2: Delete all files older than 12 months (365 days) with no exceptions
    if age.days > 365:
        return True
    
    # Rule 1: Delete files older than 7 days, except if created on the 1st day of the month
    if age.days > 7:
        # Check if file was created on the 1st day of the month
        if file_date.day != 1:
            return True
    
    return False

def cleanup_backup_directory(directory_path):
    """
    Clean up files in the specified directory based on age rules.
    
    Args:
        directory_path: Path to the backup directory
    """
    directory = Path(directory_path)
    
    # Check if directory exists
    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory '{directory_path}' does not exist or is not a directory.")
        return
    
    # Get current time
    now = datetime.datetime.now()
    
    # Statistics
    deleted_count = 0
    kept_count = 0
    error_count = 0
    
    print(f"Cleaning up directory: {directory_path}")
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Iterate through all files in the directory
    for file_path in directory.iterdir():
        if file_path.is_file():
            try:
                if should_delete_file(file_path, now):
                    # Delete the file
                    file_path.unlink()
                    print(f"DELETED: {file_path.name}")
                    deleted_count += 1
                else:
                    print(f"KEPT:   {file_path.name}")
                    kept_count += 1
            except Exception as e:
                print(f"ERROR:  {file_path.name} - {str(e)}")
                error_count += 1
    
    # Print summary
    print("-" * 60)
    print(f"Summary: {deleted_count} files deleted, {kept_count} files kept, {error_count} errors")

def main():
    """Main function to run the cleanup."""
    backup_dir = '/home/simon/backup'
    cleanup_backup_directory(backup_dir)

if __name__ == "__main__":
    main()
