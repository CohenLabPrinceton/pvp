import time
import vent.io as io
import numpy as np
import matplotlib.pyplot as plt 

hal = io.Hal(config_file='vent/io/config/devices.ini')

n_ramp_steps = 50

# Initialize arrays to store pressure log
store_len = 1000
dt        = 0.1
waittime  =  5    # seconds  
p_store = np.zeros((store_len,6))
idx = 0


def cycle(idx, store_len):

    # Ramp up to PIP over inhale time
    for i in range(n_ramp_steps+1):
        # Get "valve openness" setpoint
        setpnt = int(50 / n_ramp_steps * i)
        print(np.round(setpnt, 2))
        
        # Set duty cycle via response curve in hardware abstraction layer ("hal")
        hal.setpoint_in = max(min(100, setpnt), 0)
        hal.setpoint_ex = 0

        # Read and log pressure
        p = hal.pressure
        qin = hal.flow_in
        qout = hal.flow_ex
        setin = hal.setpoint_in
        setex = hal.setpoint_ex

        if idx < store_len:
            p_store[idx,:] = np.array([time.time(), p, setin, setex, qin, qout])
            idx += 1
        # Stay at this duty cycle for 0.1 seconds 
        time.sleep(dt)
    
    # Close valve and wait 3 seconds for "exhale"
    hal.setpoint_in = 0
    hal.setpoint_ex = 1
    for t in range(np.int(waittime/dt)):
        p_store[idx,:] = np.array([time.time(), p, setin, setex, qin, qout])
        time.sleep(dt)  
        idx += 1

    return idx       


try:
    while True:
        idx = cycle(idx, store_len)
except KeyboardInterrupt:
    print("Ctl C pressed - ending program")

    #make sure valves are closed
    hal.setpoint_in = 0
    hal.setpoint_ex = 1
    # 
    np.save("data", p_store)

finally:
    hal._inlet_valve.close()
    hal._control_valve.close()


# import pylab as pl
# import numpy as np
# np.load("data.npy")
# tt = p_store[:,0] - np.min(p_store[:,0])
# pl.plot(tt, p_store(:,2), "label = pressure")
# xlabel("time [s]")