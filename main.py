#!/usr/bin/env python

# This is the main script. The UI people can create this for us.
# It calls to main_control which reads in sensor data and controls the system.
import time
import sensors
import alarms
import controller
import main_control
import helper
import argparse

SAMPLETIME = 0.01


def _main_loop():
    # Initialize sensor reading/tracking and UI structures:
    jp = sensors.JuliePlease()  # Provides a higher-level sensor interface.
    tracker = sensors.SensorTracking(jp)  # Initialize class for logging sensor readings.
    alarm_bounds = alarms.AlarmBounds()  # Intiialize object for storing alarm trigger bounds.
    control = controller.Controller()

    try:
        while True:
            # UI logic should go into this script. Callbacks needed.

            main_control.take_step(jp, tracker, alarm_bounds, control)

            # Pause until next datapoint capture
            # time.sleep(SAMPLETIME)
    except KeyboardInterrupt:
        print("Ctl C pressed - ending program")
        del control


def main_loop(args):
    if args.multi_process == True:
        raise NotImplementedError
    if args.simulation == False:
        raise NotImplementedError
    _main_loop()


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--simulation', help='running as simulation using virtual sensors and actuators',
                        action='store_true')
    parser.add_argument('--multi_process', help='running UI and controller as separate processes', action='store_true')
    return parser.parse_args()


def main():
    args = parse_cmd_args()
    main_loop(args)


if __name__ == '__main__':
    main()
