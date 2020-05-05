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

import numpy as np

##################################
# Test user interaction
# Simulate user actions with the whole intact gui

n_samples = 100

def test_gui_launch(qtbot):
    assert qt_api.QApplication.instance() is not None

    coordinator = get_coordinator(sim_mode=True, single_process=True)
    vent_gui = gui.Vent_Gui(coordinator)

    # wait for a second to let the simulation spin up and start spitting values
    qtbot.wait(1000)

    assert vent_gui.isVisible()




###################################
# Test base components

#####
# doubleslider
# default values
decimals = 5

def test_doubleslider(qtbot):
    """
    test that the doubleslider accurately represents floats
    """
    doubleslider = widgets.components.DoubleSlider(decimals=decimals)
    doubleslider.show()
    qtbot.addWidget(doubleslider)

    doubleslider.setMinimum(0)
    doubleslider.setMaximum(1)

    for i in np.random.rand(n_samples):
        test_val = np.round(i, decimals)
        doubleslider.setValue(test_val)
        assert(doubleslider.value() == test_val)

def test_doubleslider_maxmin(qtbot):

    doubleslider = widgets.components.DoubleSlider(decimals=decimals)
    doubleslider.show()
    qtbot.addWidget(doubleslider)

    multiplier = 100
    for i in range(n_samples):
        vals = np.random.rand(2)*multiplier
        min, max = np.min(vals), np.max(vals)
        min, max = np.round(min, decimals), np.round(max, decimals)

        doubleslider.setMinimum(min)
        doubleslider.setMaximum(max)

        # test that values were set correctly
        assert(doubleslider.minimum() == min)
        assert(doubleslider.maximum() == max)

        # test below min and above max
        test_min = min - np.random.rand()*multiplier
        test_max = max + np.random.rand()*multiplier

        doubleslider.setValue(test_min)
        assert(doubleslider.value() == doubleslider.minimum())
        doubleslider.setValue(test_max)
        assert(doubleslider.value() == doubleslider.maximum())


