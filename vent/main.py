#!/usr/bin/env python
import argparse
from vent.coordinator.coordinator import get_coordinator


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    # TODO: maybe we should add a mode without UI display, so this would only have command line interface?
    parser.add_argument('--simulation', help='running as simulation using virtual sensors and actuators',
                        action='store_true')
    parser.add_argument('--single_process', help='running UI and controller within one process', action='store_true')
    return parser.parse_args()


def main():
    args = parse_cmd_args()
    coordinator = get_coordinator(single_process=args.single_process, sim_mode=args.simulation)
    # TODO: gui.main(ui_control_module)


if __name__ == '__main__':
    main()
