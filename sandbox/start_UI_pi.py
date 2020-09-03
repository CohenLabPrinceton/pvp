import argparse
import sys
import os

sys.path.append("../")

from pvp import prefs
from pvp.gui.main import launch_gui
from pvp.coordinator.coordinator import get_coordinator

import pvp.io as io
import time

sim_mode = False
def main():

    try:
        coordinator = get_coordinator(single_process=False, sim_mode=sim_mode)
        app, gui = launch_gui(coordinator)
        sys.exit(app.exec_())

    except:
        print("...ending program & closing valves")
        if not sim_mode:
            time.sleep(0.01)
            HAL = io.Hal( config_file = 'pvp/io/config/devices.ini')
            for i in range(10):
                HAL.setpoint_in = 0
                HAL.setpoint_ex = 1 
                time.sleep(0.01)
        print("...done")

if __name__ == '__main__':
    main()
