import logging
from logging.handlers import RotatingFileHandler
import os

def get_logger(name:str, folder:str="log", level=logging.DEBUG) -> logging.Logger:
    os.makedirs(folder, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(os.path.join(folder, f"{name}.log"), mode="a", maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
