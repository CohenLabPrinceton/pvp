#!/usr/bin/env python

# This is the main script. The UI people can create this for us.
# It calls to main_control which reads in sensor data and controls the system.
import argparse

import gui
from ui_control_module import get_ui_control_module


#
# def _main_loop(args):
#     # TODO, process management thread, communication thread
#     # process_management_thread = threading.Thread(target=process_management_func)
#     # process_management_thread.start()
#     # process_management_thread.join()
#     ui_control_module_comm = UIControlModuleComm(args.simulation)
#     ui_thread = threading.Thread(target=gui.main, args=(ui_control_module_comm, ))
#     ui_thread.start()
#
#     control_main = main_control.MainControlSim()
#     control_main_thread = threading.Thread(target=control_main.main)
#     control_main_thread.start()
#     while True:
#         # TODO: communication with UI based on queue
#         v = control_main.get()
#         control_main.set({})
#         time.sleep(0.01)
#
#     ui_thread.join()
#     control_main_thread.join()
#
#
# def main_loop(args):
#     if args.multi_process == True:
#         raise NotImplementedError('Error: multi_process architecture not implemented')
#     if args.simulation == False:
#         raise NotImplementedError('Error: real sensor not implemented')
#     ui_control_module =
#     _main_loop(args)


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--simulation', help='running as simulation using virtual sensors and actuators',
                        action='store_true')
    parser.add_argument('--multi_process', help='running UI and controller as separate processes', action='store_true')
    return parser.parse_args()


def main():
    args = parse_cmd_args()
    ui_control_module = get_ui_control_module(single_process=args.multi_process, sim_mode=args.simulation)
    gui.main(ui_control_module)


if __name__ == '__main__':
    main()
