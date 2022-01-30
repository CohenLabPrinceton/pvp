#!/usr/bin/env python
import argparse
import sys
import os
import time
from pvp import prefs
import pvp.io as io

from pvp.gui.main import launch_gui
from pvp.coordinator.coordinator import get_coordinator


def parse_cmd_args(arg):
    parser = argparse.ArgumentParser()
    # TODO: maybe we should add a mode without UI display, so this would only have command line interface?
    parser.add_argument('--simulation',
                        help='run as simulation using virtual sensors and actuators (default: False)',
                        action='store_true')
    parser.add_argument('--single_process',
                        help='running UI and coordinator within one process (default: False)',
                        action='store_true')
    parser.add_argument('--default_controls',
                        help='set default ControlValues on start (default: False).',
                        action='store_true')
    parser.add_argument('--screenshot',
                        help='raise dummy alarms to take a screenshot!',
                        action='store_true')
    return parser.parse_args(arg)

def set_valves_save_position(args, config_file = 'pvp/io/config/devices.ini'):
    if not args.simulation:
        print("Terminating program; closing vents...")
        time.sleep(0.01)
        if config_file == None:
            HAL = io.HALMock()
        else:
            #Following line is tested in all the hal tests:
            HAL = io.Hal(config_file) # pragma: no cover
        for i in range(10):
            HAL.setpoint_in = 0
            HAL.setpoint_ex = 1
            time.sleep(0.01)
    else:
        print("Terminating simulation.")

def main(arg):
    args = parse_cmd_args(arg)         # pragma: no cover
    try:
        coordinator = get_coordinator(single_process=args.single_process, sim_mode=args.simulation)
        app, gui = launch_gui(coordinator, args.default_controls, screenshot=args.screenshot)
        sys.exit(app.exec_())
    finally: #Only in cases of errors; tested above
        set_valves_save_position(args)  # pragma: no cover


    # TODO: gui.main(ui_control_module)
    # TODO: use signal for more flexible termination, e.g.
    # signal.signal(signal.SIGINT, set_valves_to_save_position)   # Keyboard interrupt
    # signal.signal(signal.SIGTERM, set_valves_to_save_position)  # Termination signal


if __name__ == '__main__':
    main(sys.argv[1:])
