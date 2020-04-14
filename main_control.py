#!/usr/bin/env python

import time
import alarms
import helper
import threading
import sensor_tracking
import controller_sim
import sensors_sim

SAMPLETIME = 0.01

class MainControl:
    """
    Interactive with sensor/actuator, and make control decisions
    """
    def __init__(self):
        import sensors
        import controller
        # Initialize sensor reading/tracking and UI structures:
        self.jp = sensors.JuliePlease()  # Provides a higher-level sensor interface.
        self.tracker = sensors.SensorTracking(self.jp)  # Initialize class for logging sensor readings.
        self.alarm_bounds = alarms.AlarmBounds()  # Intiialize object for storing alarm trigger bounds.
        self.control = controller.Controller()

    def main(self):
        """
        This is the original code of the main.py. I move it here because by design this is internal view of controller
        :return:
        """
        try:
            while True:
                # UI logic should go into this script. Callbacks needed.
                # TODO: not need these argument passing. I just keep this for consistency
                self.take_step(self.jp, self.tracker, self.alarm_bounds, self.control)

                # Pause until next datapoint capture
                time.sleep(SAMPLETIME)
        except KeyboardInterrupt:
            print("Ctl C pressed - ending program")
            del self.control

    def take_step(self, jp, tracker, alarm_bounds, control):
        # Read all the sensors.

        # Read inputs from user.
        # TODO: UI. Will modify alarm bounds.
        # set alarm_bounds

        # Control loop. Update controller according to tracked sensor values.
        control.update_controller(jp, tracker)

        # Update sensor tracking:
        tracker.update_all_sensors()

        #Throw any alarms that need throwing.
        # TODO: the simulation value is set incorrectly, will trigger alarm
        # alarms.throw_raw_alarms(tracker, alarm_bounds)


    def get(self):
        return {}

    def set(self, map):
        pass


class MainControlSim(MainControl):
    """
    Simulation main control 
    """
    def __init__(self):
        # Initialize sensor reading/tracking and UI structures:
        # TODO: init virtual sensors, controller
        self.jp = sensors_sim.JuliePleaseSim()
        self.control = controller_sim.ControllerSim()
        # self.jp = #sensors.JuliePlease()  # Provides a higher-level sensor interface.
        self.tracker = sensor_tracking.SensorTracking(self.jp)  # Initialize class for logging sensor readings.
        self.alarm_bounds = alarms.AlarmBounds()  # Intiialize object for storing alarm trigger bounds.


