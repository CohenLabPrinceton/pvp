""" Decorators for dangerous functions

"""
from vent.common.logging import log_exception
import traceback
import functools


MAX_STACK_DEPTH = 20


def locked(func):
    """
    Wrapper to use as decorator, handle lock logic for a
    @property

    Arguments:
        func (callable): function to wrap
    """

    # define a function to return that wraps the inner
    # function around some standardized error handling
    # logic

    # use .wraps to preserve inner method identity
    @functools.wraps(func)
    def lock_wrapper(self, *args, **kwargs):
        ret = None

        try:
            self.lock.acquire()
            ret = func(self, *args, **kwargs)
        except Exception as e:
            log_exception(
                e,
                traceback.TracebackException.from_exception(e, limit=MAX_STACK_DEPTH)
            )
        finally:
            self.lock.release()

        return ret

    return lock_wrapper


def pigpio_command(func):
    @functools.wraps(func)
    def exception_catcher(self, *args, **kwargs):
        result = None
        try:
            result = func(self, *args, **kwargs)
        except Exception as e:
            log_exception(e, traceback.TracebackException.from_exception(e))
        return result

    return exception_catcher
