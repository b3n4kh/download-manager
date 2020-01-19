import logging
import sys


def configure_logging(debug):
    logger = logging.getLogger("dlmanager")
    logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)
    consol = logging.StreamHandler(sys.stdout)
    logger.addHandler(consol)
    return logger
