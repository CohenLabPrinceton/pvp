import argparse
import sys
from vent.gui import styles
from vent.gui import Vent_Gui

# Using PySide (Qt) to build GUI
from PySide2 import QtCore, QtGui, QtWidgets

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch the Ventilator GUI")
    parser.add_argument('--test',
                        dest='test',
                        help="Run in test mode? (y=1/n=0, default=0)",
                        choices=('y','n'),
                        default=0)



    args = parser.parse_args()

    gui_test = False
    if args.test in (1, True, 'y'):
        gui_test = True

    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styles.GLOBAL)
    gui = Vent_Gui(test=gui_test)
    sys.exit(app.exec_())