""" Logging functionality

"""
import traceback
import os
import logging
from logging import handlers

# some global stack param
MAX_STACK_DEPTH = 20

from vent import prefs


def init_logger(module_name: str,
                log_level: int = logging.DEBUG,
                file_handler: bool = True) -> logging.Logger:
    """
    Initialize a

    Args:
        module_name (str): module name used to generate filename and name logger
        log_level (int): one of :var:`logging.DEBUG`, :var:`logging.INFO`, :var:`logging.WARNING`, or :var:`logging.ERROR`
        file_handler (bool, str): if ``True``, (default), log in ``<logdir>/module_name.log`` .
            if ``False``, don't log to disk.

    Returns:
        :class:`logging.Logger` : Logger 4 u 2 use
    """
    logger = logging.getLogger(module_name)

    # set log level
    assert log_level in (logging.DEBUG,
                         logging.INFO,
                         logging.WARNING,
                         logging.ERROR)
    logger.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # I assume this is to stop printing to stderr? why does it get a formatter then? -jls 2020-05-25
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # handler to log to disk
    # max = 8 file x 16 MB = 128 MB
    if file_handler:
        log_filename = os.path.join(prefs.get_pref('LOG_DIR'),
                                    module_name + '.log')
        fh = logging.handlers.RotatingFileHandler(
            log_filename,
            mode = 'a',
            maxBytes=16 * 2 ** 20,
            backupCount=7
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def log_exception(e, tb):
    """  # TODO: Stub exception logger. Prints exception type & traceback

    Args:
        e: Exception to log
        tb: TraceBack associated with Exception e

    """
    print("Caught the following exception:", e, " but I don't know what to do with it.")
    # print(traceback.print_tb(tb, limit=MAX_STACK_DEPTH))
    raise
