
#########################
# Imports

# python standard libraries
import os
from PySide2 import QtGui



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
    except:
        # if that fails, try to load liberation mono
        # TODO: Log this
        try:
            mono_font = QtGui.QFont('Liberation Mono')

        except:
            # otherwise get the system default mono font
            mono_font = QtGui.QFont()
            mono_font.setStyleHint(QtGui.QFont.Monospace)

    globals()['_MONO_FONT'] = mono_font

#from vent.gui.main import Vent_Gui

# modules for interacting with rest of ventilator


##########################
# GUI Class


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Launch the Ventilator GUI")
#     parser.add_argument('--test',
#                         dest='test',
#                         help="Run in test mode? (y=1/n=0, default=0)",
#                         choices=('y','n'),
#                         default=0)


    #
    # args = parser.parse_args()
    #
    # gui_test = False
    # if args.test in (1, True, 'y'):
    #     gui_test = True
    #
    # # just for testing, should be run from main
    # app = QtWidgets.QApplication(sys.argv)
    # app.setStyleSheet(styles.GLOBAL)
    # gui = Vent_Gui(test=gui_test)
    # sys.exit(app.exec_())

from vent.gui.main import Vent_Gui, launch_gui, get_gui_instance
