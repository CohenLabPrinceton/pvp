# library imports:
from time import sleep
import sensors
# This is the library for reading sensor values.
# Much is taken from https://circuitpython.readthedocs.io/projects/ads1x15/en/latest/examples.html


class JuliePleaseSim(sensors.JuliePlease):
    def __init__(self):
        pass

    def get_pressure1_reading(self):
        return 0

    def get_pressure2_reading(self):
        return 0
        
    def get_o2_reading(self):
        return 0

    def get_flow_reading(self):
        flowbytes = flowbytes = bytearray(4)
        flow_val = self.convert_raw_to_flow(flowbytes)
        return flow_val

    def get_temp_reading(self):
        return -1.0

    def get_humid_reading(self):
        return -1.0

