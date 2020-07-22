import sys
import time
import numpy as np
import pylab as pl
import tables as pytb
import os
sys.path.append('../')

Controller = get_control_module(sim_mode=False)
Controller.HAL.setpoint_ex = 1

samples = 10000
p_store = np.zeros((samples,3))
idx = 0
f = 2*pi/0.06  # 60ms period
t0 = time.time()
for t in np.arange(0, samplede):

    now = time.time()
    valveset = (np.sin(f* (now-t0))+1)*5

    Controller.HAL.setpoint_in = valveset # Max between 0 and 100
    flowex = Controller.HAL.flow_ex/60    # in l/sec

    ## And this what the controller sees
    p_store[idx,:] = np.array([time.time(), valveset, flowex])
    idx += 1


Controller.HAL.setpoint_in = 0
time.sleep(0.05)
Controller.HAL.setpoint_in = 0
time.sleep(0.05)
Controller.HAL.setpoint_ex = 1
time.sleep(0.05)
Controller.HAL.setpoint_ex = 1

np.save("delaymeasurement_sinusoid.npy", p_store)