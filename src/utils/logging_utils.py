import os
import logging

def setup_logging(log_file):
    """Set up logging configuration."""
    print(f"Attempting to set up logging with log file: {log_file}")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.getLogger().setLevel(logging.INFO)
        print(f"Logging setup completed. Log file should be at: {log_file}")
        logging.info("Logging initialized successfully")
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Log file directory exists: {os.path.exists(os.path.dirname(log_file))}")
        print(f"Log file is writable: {os.access(os.path.dirname(log_file), os.W_OK)}")
