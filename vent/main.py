#!/usr/bin/env python
import argparse
import sys
import os
from vent import prefs
from vent.gui.main import launch_gui
from vent.coordinator.coordinator import get_coordinator


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    # TODO: maybe we should add a mode without UI display, so this would only have command line interface?
    parser.add_argument('--simulation',
                        help='run as simulation using virtual sensors and actuators (default: False)',
                        action='store_true')
    parser.add_argument('--single_process',
                        help='running UI and coordinator within one process (default: False)',
                        action='store_true')
    return parser.parse_args()


def main():
    args = parse_cmd_args()
    coordinator = get_coordinator(single_process=args.single_process, sim_mode=args.simulation)
    app, gui = launch_gui(coordinator)
    sys.exit(app.exec_())


    # TODO: gui.main(ui_control_module)


if __name__ == '__main__':
    main()
