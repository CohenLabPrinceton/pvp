
#########################
# Imports

# python standard libraries
import os
from collections import OrderedDict as odict
from PySide2 import QtGui
from vent.common.values import ValueName, SENSOR
from vent.gui import styles

LIMIT_GUI_INSTANCE = True
"""
(bool): whether there hsould only be one GUI instance at a time. disabled during testing.
"""

def limit_gui(limit=None):
    if limit is None:
        return globals()['LIMIT_GUI_INSTANCE']
    else:
        globals()['LIMIT_GUI_INSTANCE'] = limit


PLOTS = odict({
    ValueName.PRESSURE: SENSOR[ValueName.PRESSURE].to_dict(),
    ValueName.TEMP: SENSOR[ValueName.TEMP].to_dict(),
    ValueName.HUMIDITY: SENSOR[ValueName.HUMIDITY].to_dict()
})
"""
Values to plot.

Should have the same key as some key in :data:`~.defaults.SENSOR`. If it does,
it will be mutually connected to the resulting :class:`.gui.widgets.Monitor_Value`
such that the set limit range is updated when the horizontal bars on the plot are updated.::

    {
        'name' (str): title of plot,
        'abs_range' (tuple): absolute limit of plot range,
        'safe_range' (tuple): safe range, will be discolored outside of this range,
        'color' (str): hex color of line (like "#FF0000")
    }
"""

PLOTS[ValueName.PRESSURE]['color'] = styles.SUBWAY_COLORS['orange']
PLOTS[ValueName.TEMP]['color'] = styles.SUBWAY_COLORS['red']
PLOTS[ValueName.HUMIDITY]['color'] = styles.SUBWAY_COLORS['blue']


########################

_GUI_INSTANCE = None

def set_gui_instance(instance):
    """
    Store the current instance of the GUI

    Arguments:
        instance (:class:`~.vent.gui.main.Vent_Gui`)
    """
    globals()['_GUI_INSTANCE'] = instance


def get_gui_instance():
    """
    Retreive the currently running instance of the GUI

    Returns:
        :class:`~.vent.gui.main.Vent_Gui`
    """
    return globals()['_GUI_INSTANCE']

###########
# Load a monospace font for displaying numbers
# Want to load an explicit font because computing the hint to find the default mono font is expensive

_MONO_FONT = None
def mono_font():
    """
    module function to return a :class:`PySide2.QtGui.QFont` to use as the mono font.

    use this instead of just making because :class:`PySide2.QtGui.QFontDatabase` can't be instantiated before the
    :class:`PySide2.QtWidgets.QApplication` is instantiated, so we load the font after the app
    """
    if globals()['_MONO_FONT'] is None:
        load_mono_font()

    return globals()['_MONO_FONT']

def load_mono_font():
    """
    Load the monospaced font and set the module-global :data:`_MONO_FONT` object.

    .. note::

        Must be called after :class:`PySide2.QtWidgets.QApplication` is instantiated!

    """
    try:
        # first try to load fira code for monospace font
        external_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'external')
        font_db = QtGui.QFontDatabase()
        font_db.addApplicationFont(os.path.join(external_dir, 'FiraCode-Regular.otf'))
        font_db.addApplicationFont(os.path.join(external_dir, 'FiraCode-Bold.otf'))
        mono_font = QtGui.QFont('Fira Code')
    except:   # pragma: no cover
        # if that fails, try to load liberation mono
        # TODO: Log this
        try:
            mono_font = QtGui.QFont('Liberation Mono')

        except:
            # otherwise get the system default mono font
            mono_font = QtGui.QFont()
            mono_font.setStyleHint(QtGui.QFont.Monospace)

    globals()['_MONO_FONT'] = mono_font


from vent.gui.main import Vent_Gui, launch_gui, get_gui_instance
