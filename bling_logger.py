import logging
import sys

LOG_FILE = "bling_monitor.log"

def setup_logger():
    """
    Configures and returns a logger that writes to both console and a file.
    """
    # Use a named logger to avoid conflicts with other libraries
    logger = logging.getLogger("bling_monitor")
    logger.setLevel(logging.INFO)

    # Prevent handlers from being added multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a formatter that includes timestamp, log level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # --- File Handler ---
    # Writes log messages to a file
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # --- Stream Handler ---
    # Writes log messages to the console (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

# --- Global Logger Instance ---
# This instance is created once and can be imported into any other module
log = setup_logger()
