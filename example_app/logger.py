"""
Custom logger
"""
import logging
import os
import sys
import time

logging.Formatter.converter = time.gmtime

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "[%(levelname)s]  %(asctime)s.%(msecs)03dZ  %(name)s:%(funcName)s:%(lineno)d  %(message)s"
LOG_FORMATTER = logging.Formatter(LOG_FORMAT, "%Y-%m-%dT%H:%M:%S")


def get_logger(name) -> logging.Logger:
    logger = logging.getLogger(name)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.formatter = LOG_FORMATTER
        logger.addHandler(handler)

    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    return logger
