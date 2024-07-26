"""File operations for the PDF download script."""

import os
import time
import logging

def rename_files_remove_splitted(download_dir):
    """Rename downloaded files to remove '_splitted' from their names."""
    downloaded_files = os.listdir(download_dir)
    for file_name in downloaded_files:
        if "_splitted" in file_name:
            new_file_name = file_name.replace("_splitted-", "")
            original_path = os.path.join(download_dir, file_name)
            new_path = os.path.join(download_dir, new_file_name)
            try:
                os.rename(original_path, new_path)
                logging.info(f"Renamed {file_name} to {new_file_name}")
            except Exception as e:
                logging.error(
                    f"Error renaming file {file_name} to {new_file_name}: {e}"
                )

def handle_permission_error(filename, attempt):
    """Handle permission errors when trying to remove a file."""
    if attempt < 2:  # If it's not the last attempt
        logging.warning(f"File {filename} is still in use. Retrying in 5 seconds...")
        time.sleep(5)
    else:
        logging.warning(f"File {filename} is still in use after 3 attempts. Skipping removal.")

def remove_crdownload_file(download_dir, filename):
    """Attempt to remove a specific .crdownload file."""
    file_path = os.path.join(download_dir, filename)
    for attempt in range(3):  # Try 3 times
        try:
            os.remove(file_path)
            logging.info(f"Removed leftover .crdownload file: {filename}")
            return
        except PermissionError:
            handle_permission_error(filename, attempt)
        except Exception as e:
            logging.error(f"Error removing .crdownload file {filename}: {str(e)}")
            return

def cleanup_crdownload_files(download_dir):
    """Remove any leftover .crdownload files in the download directory."""
    for filename in os.listdir(download_dir):
        if filename.endswith(".crdownload"):
            remove_crdownload_file(download_dir, filename)
