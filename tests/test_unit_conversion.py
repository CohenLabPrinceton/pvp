import pytest

import numpy as np

from pvp.common import unit_conversion

n_samples = 10

def test_pressure_unit_conversion():
    """dumbest test in the world lol"""

    # test converting to cmH2O and hpa
    for i in range(n_samples):
        test_val = (np.random.rand()-0.5)*1000
        assert unit_conversion.cmH2O_to_hPa(test_val) == test_val*98.0665
        assert unit_conversion.hPa_to_cmH2O(test_val) == test_val/98.0665

def test_rounded_string():
    """
    check that we don't have .0 on the end of a rounded string, that's all it does
    """

    unround_number = np.random.rand()*.8+1.1
    assert '.' not in unit_conversion.rounded_string(unround_number, 0)