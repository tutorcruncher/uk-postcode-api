import logging
import sys


def configure_logging():
    """Configure logging for the entire application"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s: %(message)s', datefmt='%H:%M:%S'))

    logger.addHandler(console_handler)

