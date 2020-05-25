#!/usr/bin/env python
import argparse
import sys
import os
from vent.gui.main import launch_gui
from vent.coordinator.coordinator import get_coordinator

VENT_DIR = None
LOG_DIR = None
DATA_DIR = None


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

def make_vent_dirs():
    """
    Make a directory to store logs, data, and user configuration in ``<user director>/vent``

    Creates::

        ~/vent
        ~/vent/logs - for storage of event and alarm logs
        ~/vent/data - for storage of waveform data
    """

    vent_dirs = []
    # root vent directory
    vent_dirs.append(os.path.join(os.path.expanduser('~'), 'vent'))
    globals()['VENT_DIR'] = vent_dirs[-1]
    # log directory
    vent_dirs.append(os.path.join(vent_dirs[0], 'logs'))
    globals()['LOG_DIR'] = vent_dirs[-1]
    # data directory
    vent_dirs.append(os.path.join(vent_dirs[0], 'data'))
    globals()['DATA_DIR'] = vent_dirs[-1]

    for vent_dir in vent_dirs:
        if not os.path.exists(vent_dir):
            os.mkdir(vent_dir)



def main():
    make_vent_dirs()
    args = parse_cmd_args()
    coordinator = get_coordinator(single_process=args.single_process, sim_mode=args.simulation)
    app, gui = launch_gui(coordinator)
    sys.exit(app.exec_())


    # TODO: gui.main(ui_control_module)


if __name__ == '__main__':
    main()
