"""
* main
* components
* control
* monitor
* plot
* status_bar


"""

import pytest

from pytestqt import qt_compat
from pytestqt.qt_compat import qt_api

from vent import gui
from vent.coordinator.coordinator import get_coordinator


def test_gui_launch(qtbot):
    assert qt_api.QApplication.instance() is not None

    coordinator = get_coordinator(sim_mode=True, single_process=True)
    vent_gui = gui.Vent_Gui(coordinator)
    assert vent_gui.isVisible()


