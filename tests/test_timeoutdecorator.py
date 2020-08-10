import time
from vent.common.utils import timeout, TimeoutException
from vent import prefs
import numpy as np
import pytest

#
#   simple test for the @timeout decorator
#

def test_timeout():

    @timeout
    def foo(sleeptime):
        time.sleep(sleeptime)

    timeout_dur = prefs.get_pref('TIMEOUT')

    for dt in np.random.rand(5)*timeout_dur: # Should be evaluated in roughly that time
        t0 = time.time()
        foo(dt)
        t1 = time.time()
        print( (t1-t0) / dt)
        print(timeout_dur)
        assert t1-t0 < 3*dt
        assert t1-t0 < timeout_dur
        
    for dt in (np.random.rand(5)*timeout_dur)+timeout_dur:        # Should be timeout, no longer than 60ms.
        t0 = time.time()
        with pytest.raises(TimeoutException):
            foo(dt)
        t1 = time.time()
        # time should be less than dt bc.. timed out..
        print( (t1-t0) / dt)
        assert t1-t0 < 3*dt

def test_timeout_return():

    @timeout
    def foo(argreturn, sleeptime):
        time.sleep(sleeptime)

        return argreturn + 1

    timeout_dur = prefs.get_pref('TIMEOUT')

    dts = np.random.rand(5) * timeout_dur
    add_nums = range(5)

    for dt, num in zip(dts, add_nums): # Should be evaluated in roughly that time
        t0 = time.time()
        ret = foo(num, dt)

        t1 = time.time()
        assert ret == num + 1
        assert t1-t0 < dt*2
        assert t1-t0 < timeout_dur

    ret = None
    dts = (np.random.rand(5)*timeout_dur)+timeout_dur

    for dt, num in zip(dts, add_nums):        # Should be timeout, no longer than 60ms.
        t0 = time.time()
        with pytest.raises(TimeoutException):
            ret = foo(num, dt)
        t1 = time.time()
        # time should be less than dt, but sometimes is a bit longer. Unclear why. Travis problem?
        print( (t1-t0) / dt)
        assert t1-t0 < 3*dt
        assert ret is None




