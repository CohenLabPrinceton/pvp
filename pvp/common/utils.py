import signal
import time
from contextlib import contextmanager
from pvp.common.loggers import init_logger
from pvp import prefs

class TimeoutException(Exception): pass

_TIMEOUT = prefs.get_pref('TIMEOUT')

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def timeout(func):
    """
    Defines a decorator for a 50ms timeout.
    Usage/Test:

        @timeout
        def foo(sleeptime):
            time.sleep(sleeptime)
        print("hello")
    """
    def wrapper(*args, **kwargs):
        try:
            with time_limit(globals()['_TIMEOUT']):
                ret = func(*args, **kwargs)
                return ret
        except TimeoutException as e:
            log_str = f'Method call timed out - Method: {func}'
            logger = init_logger('timeouts')
            logger.exception(log_str)
            raise e
    return wrapper