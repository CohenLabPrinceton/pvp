#!/usr/bin/env python
import argparse
from vent.coordinator.ui_control_module import get_ui_control_module


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    # TODO: maybe we should add a mode without UI display, so this would only have command line interface?
    parser.add_argument('--simulation', help='running as simulation using virtual sensors and actuators',
                        action='store_true')
    parser.add_argument('--multi_process', help='running UI and controller as separate processes', action='store_true')
    return parser.parse_args()


def main():
    args = parse_cmd_args()
    ui_control_module = get_ui_control_module(single_process=args.multi_process, sim_mode=args.simulation)
    # TODO: gui.main(ui_control_module)


if __name__ == '__main__':
    main()
