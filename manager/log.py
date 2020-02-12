import logging
import sys
import coloredlogs


def configure_logging(debug):
    logger = logging.getLogger("dlmanager")
    logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)
        coloredlogs.install(level='DEBUG')
    else:
        coloredlogs.install()

    consol = logging.StreamHandler(sys.stdout)
    logger.addHandler(consol)
    return logger
