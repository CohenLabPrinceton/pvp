from .pigpio_mocks import *
from vent.io.devices.valves import OnOffValve, PWMControlValve


@pytest.mark.parametrize("gpio", [1, 12])
@pytest.mark.parametrize("form", ['Normally Closed', 'Normally Open'])
def test_form(mock_pigpio_gpio, gpio, form):
    """_______________________________________________________________________________________________OnOffValve_TEST #1
     Tests the set/get interface of SolenoidBase/children
         - Initializes an OnOffValve
         - Sets a form
         - asserts form is set to expected form
    """
    valve = OnOffValve(gpio)
    valve.form = form
    assert valve.form == form
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("gpio", [1, 12])
@pytest.mark.parametrize("form", ['Normally Closed', 'Normally Open'])
def test_on_off_valve(mock_pigpio_gpio, gpio, form):
    """_______________________________________________________________________________________________OnOffValve_TEST #2
     Tests the open/close interface of an OnOffValve
         - Initializes an OnOffValve
         - records is_open
         - Opens the valve, records is_open
         - Closes the valve, records is_open
         - Asserts that the valve follows the pattern of a cycled valve with the set form
    """
    expected = [False, True, False] if form == 'Normally Closed' else [True, True, False]
    results = []
    valve = OnOffValve(gpio, form)
    results.append(valve.is_open)
    valve.open()
    results.append(valve.is_open)
    valve.close()
    results.append(valve.is_open)
    assert results == expected
    """__________________________________________________________________________________________________________
    """


# TODO test PWMControlValve, especially setpoint/response related stuff