import os
import pytest

import pvp.main

def test_parser():
    "Test parser"

    parsed_argument = pvp.main.parse_cmd_args(['--simulation'])
    assert parsed_argument.simulation

    parsed_argument = pvp.main.parse_cmd_args(['--single_process'])
    assert parsed_argument.single_process

    parsed_argument = pvp.main.parse_cmd_args(['--default_controls'])
    assert parsed_argument.default_controls

    parsed_argument = pvp.main.parse_cmd_args(['--screenshot'])
    assert parsed_argument.screenshot

@pytest.mark.timeout(10)
def test_valve_save():
    "Test shutdown for vales"

    # This should do nothing
    parsed_argument = pvp.main.parse_cmd_args(['--simulation'])
    pvp.main.set_valves_save_position(parsed_argument, None)

    parsed_argument = pvp.main.parse_cmd_args(['--single_process'])
    pvp.main.set_valves_save_position(parsed_argument, None)


# def test_main():
    # pvp.main.main()
    