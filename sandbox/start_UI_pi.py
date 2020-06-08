import argparse
import sys
import os
from vent import prefs
from vent.gui.main import launch_gui
from vent.coordinator.coordinator import get_coordinator

def main():
    coordinator = get_coordinator(single_process=False, sim_mode=False)
    app, gui = launch_gui(coordinator)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()