import argparse
import sys
import os
from vent import prefs
from vent.gui.main import launch_gui
from vent.coordinator.coordinator import get_coordinator

import vent.io as io
import time

sim_mode = True
def main():

    # coordinator = get_coordinator(single_process=False, sim_mode=sim_mode)
    # app, gui = launch_gui(coordinator)
    # sys.exit(app.exec_())

    try:
        coordinator = get_coordinator(single_process=False, sim_mode=sim_mode)
        app, gui = launch_gui(coordinator)
        sys.exit(app.exec_())

    except:
        print("...ending program & closing valves")
        
        if not sim_mode:
            time.sleep(0.01)
            HAL = io.Hal( config_file = 'vent/io/config/devices.ini')
            for i in range(10):
                HAL.setpoint_in = 0
                HAL.setpoint_ex = 1 
                time.sleep(0.01)

        print("...done")

if __name__ == '__main__':
    main()
