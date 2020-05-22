import time
import vent.io as io
import numpy as np
import matplotlib.pyplot as plt 

hal = io.Hal(config_file='vent/io/config/devices.ini')
print('PWM Frequency: ', hal._control_valve.frequency)

n_ramp_steps = 50
valve_open = 0

# Initialize arrays to store pressure log
store_len = 200
p_store = np.zeros((store_len,1))
idx = 0


def cycle(setpnt, idx, store_len):
    
    # Get cycle start time:
    p = hal.pressure
    #f = hal.flow  # to calculate flow
    

    # Ramp up to PIP over inhale time
    for i in range(n_ramp_steps+1):
        # Get "valve openness" setpoint
        setpnt = int(80 / n_ramp_steps * i)
        print(np.round(setpnt, 2))
        
        # Set duty cycle via response curve in hardware abstraction layer ("hal")
        hal.setpoint_in = max(min(100, setpnt), 0)
        
        # Read and log pressure
        p = hal.pressure
        if idx < store_len:
            p_store[idx] = p
            idx += 1
        # Stay at this duty cycle for 0.1 seconds 
        time.sleep(0.1)
                    
    # Close valve and wait 3 seconds for "exhale"
    hal.setpoint_in = 0
    time.sleep(3)     
    return idx       


try:
    while True:
        idx = cycle(valve_open, idx, store_len)
except KeyboardInterrupt:
    # Press Ctrl+C to end the program 
    print("Ctl C pressed - ending program")
    x_data = np.arange(0, len(p_store), 1)
    plt.scatter(x_data, p_store, c='r')
    plt.xlabel('Time steps')
    plt.ylabel('Pressure (cm H2O)')
    plt.show() 
finally:
    hal._inlet_valve.close()
    hal._control_valve.close()




