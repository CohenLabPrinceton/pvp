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
from time import sleep, time

from .test_alarms import fake_rule

from pytestqt import qt_compat
from pytestqt.qt_compat import qt_api

# mock before importing
from pvp import gui
from pvp.gui import styles
from pvp.gui import widgets
from pvp.common import message, values, unit_conversion, prefs
from pvp.common.values import ValueName
from pvp.coordinator.coordinator import get_coordinator
from pvp.alarm import AlarmType, AlarmSeverity, Alarm, Alarm_Manager

# from pvp.common import prefs
# prefs.set_pref('ENABLE_DIALOGS', False)


from PySide2 import QtCore, QtGui, QtWidgets

import numpy as np

##################################

# turn off gui limiting
gui.limit_gui(False)
assert gui.limit_gui() == False

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
    vent_gui = gui.PVP_Gui(coordinator, set_defaults=True)
    # vent_gui.init_controls()
    #app, vent_gui = launch_gui(coordinator)
    qtbot.addWidget(vent_gui)
    vent_gui.init_controls()
    return app, vent_gui

@pytest.fixture
def fake_sensors():
    def _fake_sensor(arg=None):
        # make an empty SensorValues
        vals = {k:0 for k in ValueName}
        vals.update({k:0 for k in message.SensorValues.additional_values})

        # since 0 is out of range for fio2, manually set it
        # FIXME: find values that by definition don't raise any of the default rules
        vals[ValueName.FIO2] = 80

        # update with any in kwargs
        if arg:
            for k, v in arg.items():
                vals[k] = v

        sensors = message.SensorValues(vals=vals)

        return sensors
    return _fake_sensor



def test_gui_launch(qtbot):


    app = qt_api.QApplication.instance()
    app.setStyle('Fusion')
    app.setStyleSheet(styles.DARK_THEME)
    app = styles.set_dark_palette(app)

    coordinator = get_coordinator(sim_mode=True, single_process=False)
    vent_gui = gui.PVP_Gui(coordinator, set_defaults=False)

    qtbot.addWidget(vent_gui)

    # try to launch without setting default controls

    vent_gui.control_panel.start_button.click()
    assert not vent_gui.running
    assert not vent_gui.coordinator.is_running()

    # now set defaults and try again
    vent_gui.init_controls()
    vent_gui.control_panel.start_button.click()
    vent_gui.plot_box.set_duration(1)
    # wait for a second to let the simulation spin up and start spitting values
    qtbot.wait(2000)

    # flip the units and make sure nothing breaks
    vent_gui.control_panel.pressure_buttons['hPa'].click()
    qtbot.wait(2000)

    assert vent_gui.isVisible()
    assert vent_gui.running
    assert vent_gui.coordinator.is_running()

    vent_gui.control_panel.start_button.click()

    assert not vent_gui.running
    assert not vent_gui.coordinator.is_running()


################################
# test user interaction
#
# @pytest.mark.parametrize("test_value", [(k, v) for k, v in values.CONTROL.items() if k == values.ValueName.PIP] )
@pytest.mark.parametrize('test_units', ('cmH2O', 'hPa'))
@pytest.mark.parametrize("test_value", [(k, v) for k, v in values.DISPLAY_CONTROL.items() if k!=values.ValueName.IE_RATIO])
def test_gui_controls(qtbot, spawn_gui, test_value, test_units):
    """
    test setting controls in all the ways available to the GUI

    from the :class:`~pvp.gui.widgets.control.Control` widget:

        * :class:`~pvp.gui.widgets.components.EditableLabel` - setting label text
        * setting slider value
        * using :meth:`~pvp.gui.main.PVP_Gui.set_value`


    Args:
        qtbot:
        spawn_gui:
        test_value:


    """
    value_name = test_value[0]
    value_params = test_value[1]

    # mercifully skip pointless tests
    if test_units == "hPa" and value_name not in (ValueName.PIP, ValueName.PEEP):
        return

    app, vent_gui = spawn_gui

    # if one of the cycle variables, make sure we click the other one as being autocalculated
    if value_name == values.ValueName.INSPIRATION_TIME_SEC:
        vent_gui.control_panel.cycle_buttons[values.ValueName.BREATHS_PER_MINUTE].click()
    elif value_name == values.ValueName.BREATHS_PER_MINUTE:
        vent_gui.control_panel.cycle_buttons[values.ValueName.INSPIRATION_TIME_SEC].click()



    vent_gui.control_panel.pressure_buttons[test_units].click()

    vent_gui.start()
    vent_gui.timer.stop()
    vent_gui.control_panel.lock_button.click()
    # stop controller because it will do funny things like change the PIP setting on us to correct for a HAPA with our random ass settings
    vent_gui.coordinator.stop()


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
        #
        # qtbot.keyPress(control_widget.set_value_label.lineEdit, QtCore.Qt.Key_Enter, 1)
        # qtbot.keyRelease(control_widget.set_value_label.lineEdit, QtCore.Qt.Key_Enter, 1)

        control_value = vent_gui.coordinator.get_control(value_name)

        if control_widget._convert_out:
            test_value = control_widget._convert_out(test_value)
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
            if control_widget._convert_out:
                test_value = control_widget._convert_out(test_value)
            # we expect some slop from the slider
            assert np.isclose(control_value.value, test_value, rtol=.1)

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
            test_value = np.mean(test_values)
            # if control_widget._convert_out:
            #     test_value = control_widget._convert_out(test_value)
            assert np.isclose(control_value.value, test_value)

    # should be one or the other
    else:
        assert False

    # from set_value
    for i in range(n_samples):
        test_value = gen_test_value()
        vent_gui.set_value(test_value, value_name = value_name)

        control_value = vent_gui.coordinator.get_control(value_name)
        assert(control_value.value == test_value)

def test_VTE_set(qtbot, spawn_gui):
    app, vent_gui = spawn_gui

    vent_gui.start()
    vent_gui.timer.stop()
    vent_gui.control_panel.lock_button.click()

    control_widget = vent_gui.monitor[ValueName.VTE.name]

    # record some VTEs n shit
    for i in range(n_samples):
        # press record
        assert (control_widget.toggle_button.isChecked() == False)
        control_widget.toggle_button.click()
        assert (control_widget.toggle_button.isChecked() == True)
        # feed it 10 test values
        test_values = []
        for j in range(10):
            new_test_value = np.random.random()*2+1
            test_values.append(new_test_value)
            control_widget.update_sensor_value(new_test_value)

        # stop recording and check the value
        control_widget.toggle_button.click()
        assert (control_widget.toggle_button.isChecked() == False)
        control_value = vent_gui._state['controls'][ValueName.VTE.name]
        assert control_value == np.mean(test_values)


@pytest.mark.parametrize("test_value", [(k, v) for k, v in values.VALUES.items() if k in \
                                        (ValueName.BREATHS_PER_MINUTE,
                                         ValueName.INSPIRATION_TIME_SEC,
                                         ValueName.IE_RATIO,
                                         )])
def test_autoset_cycle(qtbot, spawn_gui, test_value):
    value_name = test_value[0]
    value_params = test_value[1]

    app, vent_gui = spawn_gui

    if value_name == ValueName.BREATHS_PER_MINUTE:
        vent_gui.control_panel.cycle_buttons[ValueName.BREATHS_PER_MINUTE].click()

        assert vent_gui._autocalc_cycle == ValueName.BREATHS_PER_MINUTE

        # set IE_RATIO and INSPIRATION_TIME_SEC
        for i in range(n_samples):
            test_ie = np.random.rand()+0.5
            test_tinsp = np.random.rand()*3

            vent_gui.set_value(test_ie, ValueName.IE_RATIO)
            vent_gui.set_value(test_tinsp, ValueName.INSPIRATION_TIME_SEC)

            ret_tinsp = vent_gui.coordinator.get_control(ValueName.INSPIRATION_TIME_SEC).value
            ret_rr = vent_gui.coordinator.get_control(ValueName.BREATHS_PER_MINUTE).value
            assert ret_tinsp == test_tinsp
            assert ret_rr == 1/(test_tinsp + (test_tinsp/test_ie)) * 60

    elif value_name == ValueName.INSPIRATION_TIME_SEC:
        vent_gui.control_panel.cycle_buttons[ValueName.INSPIRATION_TIME_SEC].click()

        assert vent_gui._autocalc_cycle == ValueName.INSPIRATION_TIME_SEC

        for i in range(n_samples):
            test_ie = np.random.rand()+0.5
            test_rr = np.random.rand()*20+10

            vent_gui.set_value(test_ie, ValueName.IE_RATIO)
            vent_gui.set_value(test_rr, ValueName.BREATHS_PER_MINUTE)

            ret_tinsp = vent_gui.coordinator.get_control(ValueName.INSPIRATION_TIME_SEC).value
            ret_rr = vent_gui.coordinator.get_control(ValueName.BREATHS_PER_MINUTE).value
            assert ret_tinsp == (1/(test_rr/60)) / (1+1/test_ie)
            assert ret_rr == test_rr

    elif value_name == ValueName.IE_RATIO:
        # the easy one

        vent_gui.control_panel.cycle_buttons[ValueName.IE_RATIO].click()

        assert vent_gui._autocalc_cycle == ValueName.IE_RATIO

        for i in range(n_samples):
            test_tinsp = np.random.rand()*3
            test_rr = np.random.rand() * 20 + 10

            vent_gui.set_value(test_tinsp, ValueName.INSPIRATION_TIME_SEC)
            vent_gui.set_value(test_rr, ValueName.BREATHS_PER_MINUTE)

            ret_tinsp = vent_gui.coordinator.get_control(ValueName.INSPIRATION_TIME_SEC).value
            ret_rr = vent_gui.coordinator.get_control(ValueName.BREATHS_PER_MINUTE).value
            assert ret_tinsp == test_tinsp
            assert ret_rr == test_rr

def test_alarm_manager_signals(qtbot, spawn_gui):
    # ensure test alarm_manager.update
    # TODO: This
    pass

def test_handle_controller_alarm(qtbot, spawn_gui):
    # TODO: This
    pass

def test_save_restore_gui_state(qtbot, spawn_gui):
    # TODO: This
    pass

def test_raise_alarm_card(qtbot, spawn_gui, fake_sensors):
    app, vent_gui = spawn_gui

    # throw a hapa and make sure the alarm card shows up
    uh_oh = fake_sensors()
    vent_gui.alarm_manager.update(uh_oh)
    # there will be some alarms because we dont have a way of generating safe values yet, but HAPA wont be in them
    assert not any([a.alarm_type == AlarmType.HIGH_PRESSURE for a in vent_gui.alarm_bar.alarms])

    # now poppa hapa
    uh_oh['PRESSURE'] = 10000
    vent_gui.alarm_manager.update(uh_oh)

    assert any([a.alarm_type == AlarmType.HIGH_PRESSURE for a in vent_gui.alarm_bar.alarms])

def test_gui_main_etc(qtbot, spawn_gui):

    app, vent_gui = spawn_gui

    # test setting update period
    vent_gui.update_period = 0.10
    assert vent_gui.update_period == 0.10
    assert vent_gui.timer.interval() == 0.10 * 1000 # (in ms)

    # test appearing and disappearing plots
    plot_key = list(values.PLOTS.keys())[0]
    plot_visible = vent_gui.plot_box.plots[plot_key.name].isVisible()

    vent_gui.plot_box.selection_buttons[plot_key.name].click()
    visible_now = vent_gui.plot_box.plots[plot_key.name].isVisible()
    assert plot_visible != visible_now

    vent_gui.plot_box.selection_buttons[plot_key.name].click()
    how_about_now = vent_gui.plot_box.plots[plot_key.name].isVisible()
    assert plot_visible == how_about_now

#########################
# Test control panel
def test_pressure_unit_conversion(qtbot, spawn_gui, fake_sensors):
    app, vent_gui = spawn_gui

    vent_gui.control_panel.start_button.click()
    vent_gui.timer.stop()

    sensor = fake_sensors({ValueName.PRESSURE: 10})
    vent_gui.update_gui(sensor)
    vent_gui.timer.stop()

    assert vent_gui.monitor[ValueName.PRESSURE.name].sensor_value == 10
    assert vent_gui.plot_box.plots[ValueName.PRESSURE.name]


    vent_gui.control_panel.pressure_buttons['hPa'].click()

    # get display text and compare
    display_widget = vent_gui.monitor[ValueName.PRESSURE.name]
    display_widget.timed_update()
    display_text = display_widget.sensor_label.text()

    assert display_text == unit_conversion.rounded_string(unit_conversion.cmH2O_to_hPa(10), display_widget.decimals)

    vent_gui.control_panel.pressure_buttons['cmH2O'].click()

    # TODO: test if shit is displayed like all back to normal like

def test_set_breath_detection(qtbot, spawn_gui):
    app, vent_gui = spawn_gui

    breath_detection = prefs.get_pref('BREATH_DETECTION')

    assert vent_gui.get_breath_detection() == breath_detection
    assert vent_gui.control_panel.breath_detection_button.isChecked() == breath_detection

    breath_detection = not breath_detection

    vent_gui.control_panel.breath_detection_button.click()

    assert vent_gui.get_breath_detection() == breath_detection
    assert vent_gui.control_panel.breath_detection_button.isChecked() == breath_detection

#######################
# alarm bar

def test_alarm_bar(qtbot, fake_rule):

    alarm_bar = widgets.Alarm_Bar()

    alarm_manager = Alarm_Manager()
    alarm_manager.reset()
    alarm_manager.rules = {}
    alarm_manager.load_rule(fake_rule())

    # make callback to catch emitted alarms
    global alarms_emitted
    alarms_emitted = []

    def alarm_cb(alarm):
        assert isinstance(alarm, Alarm)
        global alarms_emitted
        alarms_emitted.append(alarm)

    alarm_manager.add_callback(alarm_cb)

    qtbot.addWidget(alarm_bar)

    # raise alarms
    low = Alarm(alarm_type=AlarmType.HIGH_PRESSURE,
                severity=AlarmSeverity.LOW, latch=False)
    med = Alarm(alarm_type = AlarmType.LOW_PEEP,
                severity=AlarmSeverity.MEDIUM, latch=False)
    high = Alarm(alarm_type = AlarmType.LOW_VTE,
                 severity=AlarmSeverity.HIGH, latch=False)

    alarm_bar.add_alarm(med)
    alarm_bar.add_alarm(low)
    alarm_bar.add_alarm(high)

    # test reordering
    assert alarm_bar.alarms == [low, med, high]
    assert alarm_bar.sound_player.playing

    # clear alarms
    alarm_bar.clear_alarm(alarm=med)
    alarm_bar.clear_alarm(alarm_type=high.alarm_type)
    alarm_bar.clear_alarm(alarm=low)

    assert alarm_bar.alarms == []
    assert alarm_bar.sound_player.playing == False

    # add an alarm and replace it with another of the same type
    med_hapa = Alarm(alarm_type=AlarmType.HIGH_PRESSURE,
                severity=AlarmSeverity.MEDIUM, latch=False)
    alarm_bar.add_alarm(low)
    alarm_bar.add_alarm(med_hapa)
    assert alarm_bar.alarms == [med_hapa]
    assert alarm_bar.sound_player.playing == True

    # get an error if try to clear nothing
    with pytest.raises(ValueError):
        alarm_bar.clear_alarm()

    # mute the sound
    alarm_bar.mute_button.click()
    assert alarm_bar.sound_player._muted
    assert not alarm_bar.sound_player.playing

    alarm_bar.mute_button.click()
    assert not alarm_bar.sound_player._muted
    assert alarm_bar.sound_player.playing

    # dismiss the alarm
    alarm_bar.alarm_cards[0].close_button.click()
    # check that we get an alarm with alarmseverity off.
    # the GUI would clear this alarm if so
    assert alarms_emitted[-1].alarm_type == AlarmType.HIGH_PRESSURE
    assert alarms_emitted[-1].severity == AlarmSeverity.OFF

    alarm_manager.reset()
    alarm_manager.rules = {}
    alarm_manager.dependencies = {}
    alarm_manager.load_rules()

###################################
# Test base components

#####
# doubleslider
#
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
        assert doubleslider._minimum() == int(np.round(doubleslider.minimum() * doubleslider._multi))
        assert doubleslider._maximum() == int(np.round(doubleslider.maximum() * doubleslider._multi))

        # test below min and above max
        test_min = min - np.random.rand()*multiplier
        test_max = max + np.random.rand()*multiplier

        doubleslider.setValue(test_min)
        assert(doubleslider.value() == doubleslider.minimum())
        doubleslider.setValue(test_max)
        assert(doubleslider.value() == doubleslider.maximum())

def test_editable_label(qtbot):
    label = widgets.components.EditableLabel()
    qtbot.addWidget(label)

    test_val = str(1.0)
    label.setText(test_val)

    assert label.text() == test_val
    assert not label._editing

    # click and edit label
    qtbot.mouseClick(label.label, QtCore.Qt.LeftButton, delay=10)
    assert label._editing
    assert label.label.isHidden()
    assert not label.lineEdit.isHidden()
    assert label.lineEdit.text() == test_val

    new_text = "2.0"
    qtbot.keyClicks(label.lineEdit, new_text)

    with qtbot.waitSignal(label.textChanged, timeout=1000) as emitted_text:
        qtbot.keyClick(label.lineEdit, QtCore.Qt.Key_Enter, delay=10)

    assert emitted_text.args == [new_text]

    assert label.text() == new_text
    assert not label._editing
    assert not label.label.isHidden()
    assert label.lineEdit.isHidden()

    # test escape
    qtbot.mouseClick(label.label, QtCore.Qt.LeftButton, delay=10)
    assert label._editing
    assert label.label.isHidden()
    assert not label.lineEdit.isHidden()

    escape_text = "3.0"
    qtbot.keyClicks(label.lineEdit, escape_text)
    qtbot.keyClick(label.lineEdit, QtCore.Qt.Key_Escape, delay=10)
    assert not label._editing
    assert not label.label.isHidden()
    assert label.lineEdit.isHidden()
    assert label.text() == new_text

    # test is_editable
    label.setEditable(False)
    qtbot.mouseClick(label.label, QtCore.Qt.LeftButton, delay=10)
    assert not label._editing
    assert not label.label.isHidden()
    assert label.lineEdit.isHidden()

