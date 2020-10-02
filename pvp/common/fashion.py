""" Decorators for dangerous functions

"""
from pvp.common.loggers import init_logger
import traceback
import functools

def pigpio_command(func):
    @functools.wraps(func)
    def exception_catcher(self, *args, **kwargs):
        result = None
        try:
            result = func(self, *args, **kwargs)
        except Exception as e:
            init_logger(__name__).exception(traceback.TracebackException.from_exception(e))
            raise e
        return result

    return exception_catcher
