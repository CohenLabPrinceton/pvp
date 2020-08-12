import time
import pvp.io as io
import numpy as np
import matplotlib.pyplot as plt 

hal = io.Hal(config_file='pvp/io/config/devices.ini')

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
        # Get "valve openness" setpoin.t
        setpnt = int(20 / n_ramp_steps * i)
        
        # Set duty cycle via response curve in hardware abstraction layer ("hal")
        hal.setpoint_in = max(min(100, setpnt), 0)
        hal.setpoint_ex = 0

        # Read and log pressure
        p = hal.pressure
        qin = hal.flow_in
        qout = hal.flow_ex
        setin = hal.setpoint_in
        setex = hal.setpoint_ex

        print([np.round(setpnt, 2), p])

        if idx < store_len:
            p_store[idx,:] = np.array([time.time(), p, setin, setex, qin, qout])
            idx += 1
        # Stay at this duty cycle for 0.1 seconds 
        time.sleep(dt)
    
    # Close valve and open expiratory valve
    for t in range(np.int(waittime/dt)):
        hal.setpoint_in = 0
        hal.setpoint_ex = 1

        p = hal.pressure
        qin = hal.flow_in
        qout = hal.flow_ex
        setin = hal.setpoint_in
        setex = hal.setpoint_ex

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
    hal.setpoint_ex = 0
    # 
    np.save("data_openloop", p_store)

    hal._inlet_valve.close()
    hal._control_valve.close()
    if (hal.setpoint_in is not 0) or (hal.setpoint_ex is not 0):
        print("Cannot close vents:")
        print("Ex: " + str(hal.setpoint_ex ))
        print("In: " + str(hal.setpoint_in ))
