"""
test objects
* main
* components
* control
* monitor
* plot
* status_bar

test types
* user interaction
* flooding


"""

import pytest

from pytestqt import qt_compat
from pytestqt.qt_compat import qt_api

from vent import gui
from vent.gui import widgets
from vent.coordinator.coordinator import get_coordinator


##################################
# Test user interaction
# Simulate user actions with the whole intact gui

def test_gui_launch(qtbot):
    assert qt_api.QApplication.instance() is not None

    coordinator = get_coordinator(sim_mode=True, single_process=True)
    vent_gui = gui.Vent_Gui(coordinator)

    # wait for a second to let the simulation spin up and start spitting values
    qtbot.wait(5000)

    assert vent_gui.isVisible()




###################################
# Test base components

def test_doubleslider(qtbot):
    pass
