import numpy as np
import pytest

from pvp.common import values
from pvp.common.message import ControlSetting, SensorValues



@pytest.mark.parametrize("control_setting_name", values.CONTROL.keys())
def test_control_settings(control_setting_name):
    name = str(control_setting_name)  #Make sure that control_settings are also cool as a string
    print(name)

    assert ControlSetting(name=name, value=np.random.random(), min_value = np.random.random(), max_value = np.random.random())
    assert ControlSetting(name=name, value=None, min_value = None, max_value = None)


    # assert c_read.timestamp == c.timestamp
