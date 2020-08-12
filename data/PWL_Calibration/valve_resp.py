import time
import pvp.io as io
import numpy as np
import matplotlib.pyplot as plt
import random
import pandas as pd

hal = io.Hal(config_file='pvp/io/config/devices.ini')
hal._flow_sensor_in.maxlen_data = 1024 
SAMPLE_TIME = 0.003

'''
Plots the valve response. 
This will be used to ease controller implementation. 
'''

'''
adc = iodev.ADS1115(pig=pig)
p4v = iodev.P4vMini(adc,MUX=0)
sfm = iodev.SFM3200(pig=pig)
'''
'''
pValve = iodev.PWMControlValve(pin=12,frequency=1000,pig=pig)
inlet  = iodev.SolenoidValve(pin=27,pig=pig)
'''
hal._control_valve.duty = 0.0

n_to_avg = 20
avg_store = np.zeros((n_to_avg, 1))
    
print('Do it')
store_dc_flow = np.zeros((101,3))

n_steps = 100
for i in range(n_steps+1):
    dc =1.0 / n_steps * i
    hal._control_valve.duty = dc
    time.sleep(2)
    hal._flow_sensor_in.update()
    flow = hal._flow_sensor_in.data[0,1]
    
    for j in range(n_to_avg):
        hal._flow_sensor_in.update()
        avg_store[j] = hal._flow_sensor_in.data[0,1]

    avg = np.mean(avg_store)
    print(avg)
    
    store_dc_flow[i,0] = dc
    store_dc_flow[i,1] =avg
    
time.sleep(5)

avg_store = np.zeros((n_to_avg, 1))
    
for i in range(n_steps+1):
    dc = 1.0 - 1.0 / n_steps * i
    hal._control_valve.duty = dc
    time.sleep(2)
    hal._flow_sensor_in.update()
    flow = hal._flow_sensor_in.data[0,1]
    
    for j in range(n_to_avg):
        hal._flow_sensor_in.update()
        avg_store[j] = hal._flow_sensor_in.data[0,1]

    avg = np.mean(avg_store)
    print(avg)
    
    store_dc_flow[100-i,2] =avg
    
np.savetxt("./sandbox/response_data/valve_response_dlite_setup.csv", store_dc_flow, delimiter=",")
    
hal._control_valve.duty = 0.0




















