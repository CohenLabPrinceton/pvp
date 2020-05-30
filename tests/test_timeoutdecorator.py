import time
from vent.common.utils import timeout


#
#   simple test for the @timeout decorator
#

def test_timeout():

    @timeout
    def foo(sleeptime):
        time.sleep(sleeptime)

    for dt in [0.05, 0.01, 0.03, 0.04]: # Should be evaluated in roughly that time
        t0 = time.time()
        foo(dt)
        t1 = time.time()
        assert t1-t0 < dt*1.5
        
    for dt in [0.05, 0.07, 0.2]:        # Should be timeout, no longer than 60ms.
        t0 = time.time()
        foo(dt)
        t1 = time.time()
        assert t1-t0 < 0.06