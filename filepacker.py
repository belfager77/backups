#!/usr/bin/env python3

import os
import tarfile
from datetime import datetime
import argparse
import logging

def setup_logging():
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def create_backup(source_dir=None, backup_base_dir=None, verbose=False):
    """
    Create a compressed backup of the source directory
    
    Args:
        source_dir (str): Source directory to backup
        backup_base_dir (str): Directory where backup will be saved
        verbose (bool): If True, print detailed information
    """
    
    # Set default paths if not provided
    if source_dir is None:
        source_dir = '/home/simon/Documents'
    if backup_base_dir is None:
        backup_base_dir = '/home/simon/backup'
    
    # Create backup directory if it doesn't exist
    try:
        os.makedirs(backup_base_dir, exist_ok=True)
    except PermissionError:
        logging.error(f"Permission denied: Cannot create directory '{backup_base_dir}'")
        return False
    
    # Generate filename with current date
    current_date = datetime.now().strftime('%Y%m%d')
    backup_filename = f"{current_date}.tar.gz"
    backup_path = os.path.join(backup_base_dir, backup_filename)
    
    try:
        # Check if source directory exists
        if not os.path.exists(source_dir):
            logging.error(f"Source directory '{source_dir}' does not exist.")
            return False
        
        # Check if source directory is readable
        if not os.access(source_dir, os.R_OK):
            logging.error(f"Permission denied: Cannot read source directory '{source_dir}'")
            return False
        
        # Count files before backup
        file_count = sum([len(files) for r, d, files in os.walk(source_dir)])
        
        logging.info(f"Starting backup of '{source_dir}'")
        logging.info(f"Found {file_count} files to backup")
        logging.info(f"Creating archive: {backup_path}")
        
        # Create compressed archive
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        
        # Verify the backup was created
        if os.path.exists(backup_path):
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)
            
            logging.info(f"Backup completed successfully!")
            logging.info(f"File: {backup_path}")
            logging.info(f"Size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
            
            if verbose:
                # List contents of the archive
                with tarfile.open(backup_path, "r:gz") as tar:
                    members = tar.getmembers()
                    logging.info(f"Archive contains {len(members)} items")
            
            return True
        else:
            logging.error("Backup file was not created.")
            return False
            
    except PermissionError as e:
        logging.error(f"Permission denied: {e}")
        return False
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return False

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Create a compressed backup of Documents directory')
    parser.add_argument('-s', '--source', default='/home/simon/Documents',
                        help='Source directory to backup (default: /home/simon/Documents)')
    parser.add_argument('-d', '--destination', default='/home/simon/backup',
                        help='Destination directory for backup (default: /home/simon/backup)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show verbose output')
    
    args = parser.parse_args()
    
    setup_logging()
    
    success = create_backup(
        source_dir=args.source,
        backup_base_dir=args.destination,
        verbose=args.verbose
    )
    
    if success:
        logging.info("Backup process completed successfully")
    else:
        logging.error("Backup process failed")
        exit(1)

if __name__ == "__main__":
    main()
