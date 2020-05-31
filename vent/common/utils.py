import signal
import time
from contextlib import contextmanager

class TimeoutException(Exception): pass

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
            with time_limit(0.05):
                func(*args, **kwargs)
        except TimeoutException as e:
            print("Timed out!")
    return wrapper