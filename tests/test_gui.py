"""
test objects
* main
* components
* control
* monitor
* plot
* control_panel

test types
* user interaction
* flooding


"""

from copy import copy
import pdb

import pytest
from time import sleep


from pytestqt import qt_compat
from pytestqt.qt_compat import qt_api

# mock before importing
from pvp import gui
from pvp.gui import styles
from pvp.gui import widgets
from pvp.common import message, values
from pvp.coordinator.coordinator import get_coordinator

# from pvp.common import prefs
# prefs.set_pref('ENABLE_DIALOGS', False)


from PySide2 import QtCore, QtGui, QtWidgets

import numpy as np

##################################

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

@pytest.fixture()
def spawn_gui(qtbot):

    assert qt_api.QApplication.instance() is not None

    app = qt_api.QApplication.instance()
    app.setStyle('Fusion')
    app.setStyleSheet(styles.DARK_THEME)
    app = styles.set_dark_palette(app)

    coordinator = get_coordinator(sim_mode=True, single_process=False)
    vent_gui = gui.Vent_Gui(coordinator, set_defaults=True)
    # vent_gui.init_controls()
    #app, vent_gui = launch_gui(coordinator)
    qtbot.addWidget(vent_gui)
    vent_gui.init_controls()
    return app, vent_gui




def test_gui_launch(qtbot, spawn_gui):

    app, vent_gui = spawn_gui
    vent_gui.control_panel.start_button.click()

    # wait for a second to let the simulation spin up and start spitting values
    qtbot.wait(2000)

    assert vent_gui.isVisible()
    assert vent_gui.coordinator.is_running()


################################
# test user interaction
#
# @pytest.mark.parametrize("test_value", [(k, v) for k, v in values.CONTROL.items() if k == values.ValueName.PIP] )
@pytest.mark.parametrize("test_value", [(k, v) for k, v in values.DISPLAY_CONTROL.items() if k!=values.ValueName.IE_RATIO])
def test_gui_controls(qtbot, spawn_gui, test_value):
    """
    test setting controls in all the ways available to the GUI

    from the :class:`~pvp.gui.widgets.control.Control` widget:

        * :class:`~pvp.gui.widgets.components.EditableLabel` - setting label text
        * setting slider value
        * using :meth:`~pvp.gui.main.Vent_Gui.set_value`


    Args:
        qtbot:
        spawn_gui:
        test_value:


    """
    value_name = test_value[0]
    value_params = test_value[1]

    app, vent_gui = spawn_gui

    # if one of the cycle variables, make sure we click the other one as being autocalculated
    if value_name == values.ValueName.INSPIRATION_TIME_SEC:
        vent_gui.control_panel.cycle_buttons[values.ValueName.BREATHS_PER_MINUTE].click()
    elif value_name == values.ValueName.BREATHS_PER_MINUTE:
        vent_gui.control_panel.cycle_buttons[values.ValueName.INSPIRATION_TIME_SEC].click()


    vent_gui.start()
    vent_gui.timer.stop()
    vent_gui.control_panel.lock_button.click()


    abs_range = value_params.abs_range
    safe_range = value_params.safe_range

    # generate target value
    def gen_test_value():
        test_value = np.random.rand()*(safe_range[1]-safe_range[0]) + safe_range[0]
        test_value = np.round(test_value, value_params.decimals)
        return test_value

    ####
    # test setting controls from control widget
    # from editablelabel

    control_widget = vent_gui.controls[value_name.name]

    for i in range(n_samples):
        test_value = gen_test_value()

        control_widget.set_value_label.setLabelEditableAction()
        control_widget.set_value_label.lineEdit.setText(str(test_value))
        control_widget.set_value_label.returnPressedAction()
        # should call labelUpdatedAction and send to controller

        control_value = vent_gui.coordinator.get_control(value_name)

        assert(control_value.value == test_value)

    # from slider if we've got one
    if value_params.control_type == "slider":
    # toggle it open

        assert(control_widget.slider_frame.isVisible() == False)
        control_widget.toggle_button.click()
        assert(control_widget.slider_frame.isVisible() == True)

        for i in range(n_samples):
            test_value = gen_test_value()
            control_widget.slider.setValue(test_value)

            control_value = vent_gui.coordinator.get_control(value_name)
            assert(control_value.value == test_value)

    # or from the recorder if we've got one
    elif value_params.control_type == "record":
        for i in range(n_samples):
            # press record
            assert(control_widget.toggle_button.isChecked() == False)
            control_widget.toggle_button.click()
            assert (control_widget.toggle_button.isChecked() == True)
            # feed it 10 test values
            test_values = []
            for j in range(10):
                new_test_value = gen_test_value()
                test_values.append(new_test_value)
                control_widget.update_sensor_value(new_test_value)

            # stop recording and check the value
            control_widget.toggle_button.click()
            assert(control_widget.toggle_button.isChecked() == False)
            control_value = vent_gui.coordinator.get_control(value_name)
            assert control_value.value == np.mean(test_values)

    # should be one or the other
    else:
        assert False

    # from set_value
    for i in range(n_samples):
        test_value = gen_test_value()
        vent_gui.set_value(test_value, value_name = value_name)

        control_value = vent_gui.coordinator.get_control(value_name)
        assert(control_value.value == test_value)




#########################
# Test control panel
def test_pressure_unit_conversion():
    # TODO: this
    return

def test_sliders_during_unit_convertion():
    # TODO: this
    return




###################################
# Test base components

#####
# doubleslider
#
# def test_doubleslider(qtbot):
#     """
#     test that the doubleslider accurately represents floats
#     """
#     doubleslider = widgets.components.DoubleSlider(decimals=decimals)
#     doubleslider.show()
#     qtbot.addWidget(doubleslider)
#
#     doubleslider.setMinimum(0)
#     doubleslider.setMaximum(1)
#
#     for i in np.random.rand(n_samples):
#         test_val = np.round(i, decimals)
#
#         # set value inside of signal catcher to test both value and signal
#         with qtbot.waitSignal(doubleslider.doubleValueChanged, timeout=1000) as blocker:
#             doubleslider.setValue(test_val)
#
#         assert(doubleslider.value() == test_val)
#         assert(blocker.args == test_val)
#
#
# def test_doubleslider_minmax(qtbot, generic_minmax):
#
#     doubleslider = widgets.components.DoubleSlider(decimals=decimals)
#     doubleslider.show()
#     qtbot.addWidget(doubleslider)
#
#     multiplier = 100
#     for i in range(n_samples):
#         min, max = generic_minmax()
#
#         doubleslider.setMinimum(min)
#         doubleslider.setMaximum(max)
#
#         # test that values were set correctly
#         assert(doubleslider.minimum() == min)
#         assert(doubleslider.maximum() == max)
#
#         # test below min and above max
#         test_min = min - np.random.rand()*multiplier
#         test_max = max + np.random.rand()*multiplier
#
#         doubleslider.setValue(test_min)
#         assert(doubleslider.value() == doubleslider.minimum())
#         doubleslider.setValue(test_max)
#         assert(doubleslider.value() == doubleslider.maximum())
#
# #################
# # RangeSlider
#
# def test_rangeslider(qtbot, generic_minmax, generic_saferange):
#     abs_range = generic_minmax()
#     safe_range = generic_saferange()
#     print(safe_range)
#     orientation = QtCore.Qt.Orientation.Horizontal
#
#
#     rangeslider = widgets.components.RangeSlider(
#         abs_range,
#         safe_range,
#         decimals=decimals,
#         orientation=orientation)
#     rangeslider.show()
#     qtbot.addWidget(rangeslider)
#
#     # test ranges & values
#     assert(rangeslider.minimum() == abs_range[0])
#     assert(rangeslider.maximum() == abs_range[1])
#     assert(rangeslider.low == safe_range[0])
#     assert(rangeslider.high == safe_range[1])
#
#     for i in range(n_samples):
#         min, max = generic_saferange()
#         print(min, max)
#
#         with qtbot.waitSignal(rangeslider.valueChanged, timeout=1000) as blocker:
#             rangeslider.setHigh(max)
#             assert(rangeslider.high == max)
#
#             rangeslider.setLow(min)
#             assert(rangeslider.low == min)
#
# def test_rangeslider_minmax(qtbot, generic_minmax, generic_saferange):
#     abs_range = generic_minmax()
#     safe_range = generic_saferange()
#     decimals = 5
#     orientation = QtCore.Qt.Orientation.Horizontal
#
#     rangeslider = widgets.components.RangeSlider(
#         abs_range,
#         safe_range,
#         decimals=decimals,
#         orientation=orientation)
#     rangeslider.show()
#     qtbot.addWidget(rangeslider)
#
#     for i in range(n_samples):
#         abs_min, abs_max = generic_minmax()
#         safe_min, safe_max = generic_saferange()
#
#         #pdb.set_trace()
#         # Set min and max and test they were set correctly
#         rangeslider.setMinimum(abs_min)
#         assert(rangeslider.minimum() == abs_min)
#
#         rangeslider.setMaximum(abs_max)
#         assert(rangeslider.maximum() == abs_max)
#
#         # set low and high and test they were set correctly
#         rangeslider.setHigh(safe_max)
#         assert(rangeslider.high == safe_max)
#
#         rangeslider.setLow(safe_min)
#         assert(rangeslider.low == safe_min)
#
#         # try to set low and high outside of max
#         rangeslider.setHigh(abs_max + 1)
#         assert(rangeslider.high == rangeslider.maximum())
#
#         rangeslider.setLow(abs_min - 1)
#         assert(rangeslider.low == rangeslider.minimum())
#
#         # try to set low higher and high and vice versa
#         midpoint = np.round(np.mean([abs_min, abs_max]), decimals)
#         highpoint = np.round(midpoint-1, decimals)
#         lowpoint = np.round(midpoint-1-(10**-decimals), decimals)
#
#         rangeslider.setLow(midpoint)
#         rangeslider.setHigh(highpoint)
#
#         assert(rangeslider.high == highpoint)
#         assert(rangeslider.low == lowpoint)
#
#         highpoint = np.round(midpoint+1+(10**-decimals), decimals)
#         lowpoint = np.round(midpoint + 1, decimals)
#
#         rangeslider.setHigh(midpoint)
#         rangeslider.setLow(lowpoint)
#
#         assert(rangeslider.low == lowpoint)
#         assert(rangeslider.high == highpoint)
#


##########################
# keeping for good pytest-qt exmaples

# @pytest.mark.parametrize("test_value", [(k, v) for k, v in values.SENSOR.items()])
# def test_gui_monitor(qtbot, spawn_gui, test_value):


#     app, vent_gui = spawn_gui

#     vent_gui.start()
#     vent_gui.timer.stop()


#     value_name = test_value[0]
#     value_params = test_value[1]
#     abs_range = value_params.abs_range

#     # generate target value
#     def gen_test_values():
#         test_value = np.random.rand(2)*(abs_range[1]-abs_range[0]) + abs_range[0]
#         test_value = np.round(test_value, value_params.decimals)
#         return np.min(test_value), np.max(test_value)

#     monitor_widget = vent_gui.monitor[value_name.name]

#     # open the control
#     assert(monitor_widget.slider_frame.isVisible() == False)
#     monitor_widget.toggle_button.click()
#     assert (monitor_widget.slider_frame.isVisible() == True)

#     # set handles to abs_min and max so are on absolute right and left sides
#     monitor_widget.range_slider.setValue(abs_range)
#     assert(monitor_widget.range_slider.low == monitor_widget.range_slider.minimum())
#     assert (monitor_widget.range_slider.high == monitor_widget.range_slider.maximum())
#     #
#     # # move left a quarter of the way to the right
#     # widget_size = monitor_widget.range_slider.size()
#     #
#     # # get low box position
#     # low_pos = monitor_widget.range_slider.get_handle_rect(0)
#     # click_pos = low_pos.center()
#     # move_pos = copy(click_pos)
#     # move_pos.setX(move_pos.x() + (widget_size.width()/4))
#     #
#     # qtbot.mouseMove(monitor_widget.range_slider, click_pos, delay=100)
#     # qtbot.mousePress(monitor_widget.range_slider, QtCore.Qt.LeftButton, delay=200)
#     # qtbot.mouseMove(monitor_widget.range_slider, move_pos)
#     # qtbot.mouseRelease(monitor_widget.range_slider, QtCore.Qt.LeftButton, pos=move_pos, delay=200)


#     # set with range_slider
#     # for i in range(n_samples):
#     #     test_min, test_max = gen_test_values()
#     #
#     #
#     #     with qtbot.waitSignal(monitor_widget.limits_changed, timeout=1000) as blocker:
#     #         monitor_widget.range_slider.setLow(test_min)
#     #         sleep(0.01)
#     #         assert(blocker.args[0][0]==test_min)
#     #
#     #     with qtbot.waitSignal(monitor_widget.limits_changed, timeout=1000) as blocker:
#     #         monitor_widget.range_slider.setHigh(test_max)
#     #         sleep(0.01)
#     #         assert(blocker.args[0][1]==test_max)

