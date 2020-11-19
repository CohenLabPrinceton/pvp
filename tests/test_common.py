import numpy as np
import pytest

from pvp.common import values
from pvp.common.message import ControlSetting, SensorValues
from pvp.common.values import ValueName



@pytest.mark.parametrize("control_setting_name", values.CONTROL.keys())
def test_control_settings(control_setting_name):
    name = str(control_setting_name)  # Make sure that control_settings are also cool as a string
    print(name)

    assert ControlSetting(name=name, value=np.random.random(), min_value = np.random.random(), max_value = np.random.random())
    with pytest.raises( Exception ):
        assert ControlSetting(name=name, value=None, min_value = None, max_value = None)  # At least one has to be given
    with pytest.raises( Exception ):
        assert ControlSetting(name="doesnotexist", value=np.random.random(), min_value = np.random.random(), max_value = np.random.random()) # Name must exist



def test_sensor_values():
    vals  =  {  ValueName.PIP.name                  : 0,
                ValueName.PEEP.name                 : 0,
                ValueName.FIO2.name                 : 0,
                ValueName.PRESSURE.name             : 0,
                ValueName.VTE.name                  : 0,
                ValueName.BREATHS_PER_MINUTE.name   : 0,
                ValueName.INSPIRATION_TIME_SEC.name : 0,
                ValueName.FLOWOUT.name              : 0,
                'timestamp'                         : None,
                'loop_counter'                      : None,
                'breath_count'                      : 0
            }

    timestamp = None
    loop_counter = 3472
    breath_count = None

    sv = SensorValues(timestamp, loop_counter, breath_count, vals)
    assert sv.__getitem__('FIO2') == 0
    assert sv.__getitem__('loop_counter') == loop_counter

    new_val = 177
    sv.__setitem__('loop_counter', new_val)
    assert sv.__getitem__('loop_counter') == new_val

    with pytest.raises( Exception ):
        sv.__setitem__('bla', 12) # SensorValue must exist
    with pytest.raises( Exception ):
        sv.__getitem__('bla')     # Same here, SensorValue must exists


    vals  = {   ValueName.PIP.name                  : 0,
                ValueName.PEEP.name                 : 0,
                ValueName.FIO2.name                 : 0,
                ValueName.PRESSURE.name             : 0,
                ValueName.VTE.name                  : 0,
                ValueName.BREATHS_PER_MINUTE.name   : 0,
                ValueName.INSPIRATION_TIME_SEC.name : 0,
                ValueName.FLOWOUT.name              : 0}
    with pytest.raises( Exception ):
        sv = SensorValues(vals=vals)
    sv = SensorValues(timestamp=None, loop_counter=0, breath_count=0, vals=vals)
    assert sv.timestamp > 0
