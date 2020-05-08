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
import pdb

from pytestqt import qt_compat
from pytestqt.qt_compat import qt_api

from vent import gui
from vent.gui import widgets
from vent.coordinator.coordinator import get_coordinator

from PySide2 import QtCore, QtGui, QtWidgets

import numpy as np

##################################
# Test user interaction
# Simulate user actions with the whole intact gui

# turn off gui limiting
gui.limit_gui(False)

n_samples = 100
decimals = 5
global_minmax_range = (0, 100)
global_safe_range = (25, 75)

@pytest.fixture
def generic_minmax():
    """
    Make a (min, max) range of values that has some safe space in between.

    ie. min can be between 0 and 0.25*(minmax_range[1]-minmax_range[0])
    and max can similarly be above the 75% mark of the range
    Returns:

    """
    def _generic_minmax():
        abs_min = np.random.rand() * (global_minmax_range[1]-global_minmax_range[0]) * 0.25 + \
                  global_minmax_range[0]
        abs_max = np.random.rand() * (global_minmax_range[1]-global_minmax_range[0]) * 0.25 + \
                  global_minmax_range[0] + (global_minmax_range[1]-global_minmax_range[0]) * 0.75
        abs_min, abs_max = np.round(abs_min, decimals), np.round(abs_max, decimals)
        return abs_min, abs_max
    return _generic_minmax

@pytest.fixture
def generic_saferange():
    """
    Make a (min, max) range of values that has some safe space in between.

    ie. min can be between 0 and 0.25*(minmax_range[1]-minmax_range[0])
    and max can similarly be above the 75% mark of the range
    Returns:

    """
    def _generic_saferange():
        abs_min = np.random.rand() * (global_safe_range[1]-global_safe_range[0]) * 0.25 + \
                  global_safe_range[0]
        abs_max = np.random.rand() * (global_safe_range[1]-global_safe_range[0]) * 0.25 + \
                  global_safe_range[0] + (global_safe_range[1]-global_safe_range[0]) * 0.75
        abs_min, abs_max = np.round(abs_min, decimals), np.round(abs_max, decimals)
        return abs_min, abs_max
    return _generic_saferange


def test_gui_launch(qtbot):
    assert qt_api.QApplication.instance() is not None

    coordinator = get_coordinator(sim_mode=True, single_process=True)
    vent_gui = gui.Vent_Gui(coordinator)
    qtbot.addWidget(vent_gui)
    vent_gui.status_bar.start_button.click()

    # wait for a second to let the simulation spin up and start spitting values
    qtbot.wait(5000)

    assert vent_gui.isVisible()

def test_gui_launch_mp(qtbot):
    assert qt_api.QApplication.instance() is not None

    coordinator = get_coordinator(sim_mode=True, single_process=False)
    vent_gui = gui.Vent_Gui(coordinator)
    qtbot.addWidget(vent_gui)
    vent_gui.status_bar.start_button.click()

    # wait for a second to let the simulation spin up and start spitting values
    qtbot.wait(5000)

    assert vent_gui.isVisible()




###################################
# Test base components

#####
# doubleslider

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

        # set value inside of signal catcher to test both value and signal
        with qtbot.waitSignal(doubleslider.doubleValueChanged, timeout=1000) as blocker:
            doubleslider.setValue(test_val)

        assert(doubleslider.value() == test_val)
        assert(blocker.args == test_val)


def test_doubleslider_minmax(qtbot, generic_minmax):

    doubleslider = widgets.components.DoubleSlider(decimals=decimals)
    doubleslider.show()
    qtbot.addWidget(doubleslider)

    multiplier = 100
    for i in range(n_samples):
        min, max = generic_minmax()

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

#################
# RangeSlider

def test_rangeslider(qtbot, generic_minmax, generic_saferange):
    abs_range = generic_minmax()
    safe_range = generic_saferange()
    print(safe_range)
    orientation = QtCore.Qt.Orientation.Horizontal


    rangeslider = widgets.components.RangeSlider(
        abs_range,
        safe_range,
        decimals=decimals,
        orientation=orientation)
    rangeslider.show()
    qtbot.addWidget(rangeslider)

    # test ranges & values
    assert(rangeslider.minimum() == abs_range[0])
    assert(rangeslider.maximum() == abs_range[1])
    assert(rangeslider.low == safe_range[0])
    assert(rangeslider.high == safe_range[1])

    for i in range(n_samples):
        min, max = generic_saferange()
        print(min, max)

        with qtbot.waitSignal(rangeslider.valueChanged, timeout=1000) as blocker:
            rangeslider.setHigh(max)
            assert(rangeslider.high == max)

            rangeslider.setLow(min)
            assert(rangeslider.low == min)

def test_rangeslider_minmax(qtbot, generic_minmax, generic_saferange):
    abs_range = generic_minmax()
    safe_range = generic_saferange()
    decimals = 5
    orientation = QtCore.Qt.Orientation.Horizontal

    rangeslider = widgets.components.RangeSlider(
        abs_range,
        safe_range,
        decimals=decimals,
        orientation=orientation)
    rangeslider.show()
    qtbot.addWidget(rangeslider)

    for i in range(n_samples):
        abs_min, abs_max = generic_minmax()
        safe_min, safe_max = generic_saferange()

        #pdb.set_trace()
        # Set min and max and test they were set correctly
        rangeslider.setMinimum(abs_min)
        assert(rangeslider.minimum() == abs_min)

        rangeslider.setMaximum(abs_max)
        assert(rangeslider.maximum() == abs_max)

        # set low and high and test they were set correctly
        rangeslider.setHigh(safe_max)
        assert(rangeslider.high == safe_max)

        rangeslider.setLow(safe_min)
        assert(rangeslider.low == safe_min)

        # try to set low and high outside of max
        rangeslider.setHigh(abs_max + 1)
        assert(rangeslider.high == rangeslider.maximum())

        rangeslider.setLow(abs_min - 1)
        assert(rangeslider.low == rangeslider.minimum())

        # try to set low higher and high and vice versa
        midpoint = np.round(np.mean([abs_min, abs_max]), decimals)
        highpoint = np.round(midpoint-1, decimals)
        lowpoint = np.round(midpoint-1-(10**-decimals), decimals)

        rangeslider.setLow(midpoint)
        rangeslider.setHigh(highpoint)

        assert(rangeslider.high == highpoint)
        assert(rangeslider.low == lowpoint)

        highpoint = np.round(midpoint+1+(10**-decimals), decimals)
        lowpoint = np.round(midpoint + 1, decimals)

        rangeslider.setHigh(midpoint)
        rangeslider.setLow(lowpoint)

        assert(rangeslider.low == lowpoint)
        assert(rangeslider.high == highpoint)

