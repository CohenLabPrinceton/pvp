import pigpio
import time
import vent.io as io
from random import random
import numpy as np
import matplotlib.pyplot as plt 

hal = io.Hal(config_file='vent/io/config/devices.ini')

print('PWM Frequency: ', hal._control_valve.frequency)


breath_time = 10
insp_time = 5
inhale_time = insp_time / 3.0
n_ramp_steps = 50
pip = 25
KP = 1
KD = 1
KI = 0.01
valve_open = 40

store_len = 200
p_store = np.zeros((store_len,1))
setpt_store = np.zeros((store_len,1))
idx = 0

#hal._pressure_sensor.calibrate()

def cycle(valve_open, idx, store_len):
    
    # Get cycle start time:
    
    tick_cycle = time.time()
    p = hal.pressure
    f = hal.flow
    
    

    # Ramp up to PIP over inhale time
    for i in range(n_ramp_steps+1):
        tick_loop = time.time()
        setpt = pip / n_ramp_steps * i
        do_cont = 0
        
        prev_error = 0
        sum_error = 0
                
        valve_open = setpt / pip * 100
        print(valve_open)
        hal.setpoint = max(min(100, valve_open), 0)
        p = hal.pressure
        if(idx < store_len):
            p_store[idx] = p
            setpt_store[idx] = setpt
            idx += 1
        time.sleep(0.1)
        
        '''
        while(do_cont == 0):
            error = setpt - p
            valve_open += (error * KP) + (prev_error * KD) + (sum_error * KI)
            hal.setpoint = max(min(100, valve_open), 0)
            p = hal.pressure
            f = hal.flow
            
            if(idx < store_len):
                p_store[idx] = p
                setpt_store[idx] = setpt
            idx += 1
            
            print('--------------------------')
            print('PWM: %3.2f Req. Pressure: %5.4f Actual Pressure: %5.4f Flow: %5.2f '%(hal._control_valve.duty,setpt,p,f)) #,end='\r')
            tock_loop = time.time()
            if((tock_loop - tick_loop) > (inhale_time / n_ramp_steps)):
                do_cont = 1
            prev_error = error
            sum_error += error
            #time.sleep(0.005)
        '''
            
             
    hal.setpoint = 0
    time.sleep(3)     
    return idx       

    print('\n Done')

try:
    while(True):
        idx = cycle(valve_open, idx, store_len)
except KeyboardInterrupt:
    print("Ctl C pressed - ending program")
    hal._inlet_valve.close()
    hal._control_valve.close()
    # Save:
    # open a binary file in write mode
    p_file = open("./pressure_log", "wb")
    # save array to the file
    np.save(p_file, p_store)
    # close the file
    p_file.close()
    xdata = np.arange(0, len(p_store), 1)
    plt.scatter(xdata, p_store, c='r')
    #plt.scatter(xdata, setpt_store, c='b')
    plt.xlabel('Time steps')
    plt.ylabel('Pressure (cm H2O)')
    plt.show() 





