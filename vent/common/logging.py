""" Logging functionality

"""
import traceback

# some global stack param
MAX_STACK_DEPTH = 20


def log_exception(e, tb):
    """  # TODO: Stub exception logger. Prints exception type & traceback

    Args:
        e: Exception to log
        tb: TraceBack associated with Exception e

    """
    print("Caught the following exception:", e, " but I don't know what to do with it.")
    # print(traceback.print_tb(tb, limit=MAX_STACK_DEPTH))
    raise
