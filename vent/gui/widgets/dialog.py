import typing

from PySide2 import QtCore, QtGui, QtWidgets
from vent.gui import get_gui_instance
from vent.common.loggers import init_logger

def pop_dialog(message: str,
               sub_message: str = None,
               modality : QtCore.Qt.WindowModality = QtCore.Qt.NonModal,
               buttons : QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok,
               default_button : QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok
               ):
    """
    Creates a dialog box to display a message.

    .. note::

        This function does *not* call `.exec_` on the dialog so that it can be managed by the caller.

    Args:
        message (str): Message to be displayed
        sub_message (str): Smaller message displayed below main message (InformativeText)
        modality ( QtCore.Qt.WindowModality ): Modality of dialog box -
            QtCore.Qt.NonModal (default) is unblocking,
            QtCore.Qt.WindowModal is blocking
        buttons (QtWidgets.QMessageBox.StandardButton): Buttons for the window, can be ``|`` ed together
        default_button (QtWidgets.QMessageBox.StandardButton): one of ``buttons`` , the highlighted button

    Returns:
        QtWidgets.QMessageBox
    """
    msg_box = QtWidgets.QMessageBox()
    msg_box.setParent(get_gui_instance())
    msg_box.setText(message)
    if sub_message:
        msg_box.setInformativeText(sub_message)
    msg_box.setStandardButtons(buttons)
    try:
        msg_box.setDefaultButton(default_button)
    except:
        logger = init_logger(__name__)
        logger.warning(f'Could not set default button to {default_button}, provided buttons {buttons}')

    msg_box.setWindowModality(modality)

    return msg_box





