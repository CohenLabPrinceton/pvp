from typing import List
from vent.coordinator.message import SensorValues, ControlSettings, Alarm


class ControlModuleBase:
    # Abstract class for controlling hardware based on settings received
    #   Functions:
    def __init__(self):
        self.sensor_values = None
        self.control_settings = None
        self.loop_counter = None

    def get_sensors(self) -> SensorValues:
        # returns SensorValues
        # include a timestamp and loop counter
        pass

    def get_active_alarms(self) -> List[Alarm]:
        pass

    def get_logged_alarms(self) -> List[Alarm]:
        pass

    def clear_logged_alarms(self):
        pass

    def set_controls(self, control_settings: ControlSettings):
        # takes ControlSettings struct
        pass

    def start(self, controlSettings):
        # start running
        # controls actuators to achieve target state
        # determined by settings and assessed by sensor values
        pass

    def stop(self):
        # stop running
        pass


# Variables:
#   sensorValues
#   controlSettings
#   loopCounter

class ControlModuleDevice(ControlModuleBase):
    # Implement ControlModuleBase functions
    pass


class ControlModuleSimulator(ControlModuleBase):
    # Implement ControlModuleBase functions
    pass


def get_control_module(sim_mode=False):
    if sim_mode == True:
        return ControlModuleSimulator()
    else:
        return ControlModuleDevice()
