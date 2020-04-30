from PySide2 import QtGui

SUBWAY_COLORS = {
    'blue': "#0039A6",
    'lime': "#6CBE45",
    'gray': "A7A9AC",
    'orange': "#FF6319",
    'yellow': "#FCCC0A",
    'red': "#EE352E",
    'green': "#00933C",
    'purple': "#B933AD"
}

BACKGROUND_COLOR = "#111111"
TEXT_COLOR = "#EEEEEE"
CONTROL_BACKGROUND = "#FF0000"
HANDLE_HEIGHT = 10
SLIDER_WIDTH = 80
SLIDER_HEIGHT = 40
INDICATOR_WIDTH = SLIDER_WIDTH/3
SLIDER_COLOR = TEXT_COLOR
INDICATOR_COLOR = SUBWAY_COLORS['blue']
ALARM_COLOR = "#FF0000"

VALUE_SIZE = 72
NAME_SIZE = 20
UNIT_SIZE = 12
TICK_SIZE = 12

GLOBAL = f"""
QWidget {{
    font-size: 20pt;
    color: {TEXT_COLOR};
}}
"""

RANGE_SLIDER = f"""
QSlider {{
    font-size : {TICK_SIZE}px;
}}

QSlider::groove:vertical {{
    border: 1px solid #FFFFFF;
    width: {SLIDER_WIDTH}px;
}}

QSlider::handle:vertical {{
    height: {HANDLE_HEIGHT}px;
    width: 20px;
    margin: 0px -20px 0px px;
    background-color: {SLIDER_COLOR};
}}

QSlider::groove:horizontal {{
    margin: 0px, 0px, 30px, 0px;
}}

QSlider::handle:horizontal {{

}}

"""


# RANGE_SLIDER = """
# QSlider {{
#     font-size: 12px;
# }}
# QSlider::groove:vertical {{
# border: 1px solid #FFFFFF;
# width: {slider_width}px;
# }}
# QSlider::handle:vertical {{
# height: {height}px;
# width: 20px;
# margin: 0px -20px 0px px;
# background-color: {slider_color};
# }}
#
# """.format(slider_width=INDICATOR_WIDTH,
#     height=HANDLE_HEIGHT,
#            slider_color=SLIDER_COLOR)



DISPLAY_VALUE =  """
QLabel {{ 
    color: {textcolor}; 
    font-size: {value_size}pt;
}}""".format(textcolor=TEXT_COLOR,
             value_size=VALUE_SIZE)

DISPLAY_VALUE_ALARM =  """
QLabel { 
    color: #ff0000; 
    font-size: 72pt; 
    font-weight: bold;
}"""

DISPLAY_NAME = """
QLabel {{ 
    color: {textcolor}; 
    font-size: {name_size}pt;
}}""".format(textcolor=TEXT_COLOR,
             name_size=NAME_SIZE)

DISPLAY_UNITS = """
QLabel {{ 
    color: {textcolor}; 
    font-size: {unit_size}pt;
}}""".format(textcolor=TEXT_COLOR,
             unit_size=UNIT_SIZE)

DISPLAY_WIDGET = """
border-bottom: 2px solid white;
"""

CONTROL_LABEL = """
QLabel {
    font-size: 12px;
}
"""

CONTROL_VALUE =  """
QLabel {{ 
    color: {textcolor}; 
    font-size: {display_value}pt;
}}
QLineEdit {{ 
    color: {textcolor}; 
    font-size: {display_value}pt;
}}

""".format(textcolor=TEXT_COLOR,
             display_value=VALUE_SIZE)

CONTROL_BOX = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND};
    border: 1px solid #000000;
    border-radius: 4px;
    margin-top: 20px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  left: 3px;
  top: -5px;
}}
"""

TITLE_STYLE = """
font-size: 32pt;
color: {text_color};
text-align: left;
""".format(text_color=TEXT_COLOR)

DIVIDER_COLOR = "#FFFFFF"

STATUS_NORMAL = f"""
QFrame {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
}}
"""

STATUS_WARN = f"""
QFrame {{
    background-color: {SUBWAY_COLORS['orange']};
    color: {TEXT_COLOR};
}}
"""

STATUS_ALARM = f"""
QFrame {{
    background-color: {SUBWAY_COLORS['red']};
    color: {TEXT_COLOR};
}}
"""

HEARTBEAT_NORMAL = f"""
QRadioButton::indicator {{
    background: qradialgradient(cx:0, cy:0, radius:1, fx:0.5, fy:0.5, stop:0 white, stop:1 {SUBWAY_COLORS['blue']});
    border-radius: 5px;
}}

QLabel {{
    color: {TEXT_COLOR};
}}
"""

HEARTBEAT_ALARM = f"""
QRadioButton::indicator {{
    background: qradialgradient(cx:0, cy:0, radius:1, fx:0.5, fy:0.5, stop:0 white, stop:1 {SUBWAY_COLORS['red']});
    border-radius: 5px;
}}

QLabel {{
    color: {SUBWAY_COLORS['red']};
}}
"""

STATUS_BOX = f"""
QWidget {{
    background-color: {BACKGROUND_COLOR};
}}
"""


def set_dark_palette(app):
    """ Apply Dark Theme to the Qt application instance.

    borrowed from https://github.com/gmarull/qtmodern/blob/master/qtmodern/styles.py
        Args:
            app (QApplication): QApplication instance.
    """

    darkPalette = QtGui.QPalette()

    # base
    darkPalette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(TEXT_COLOR))
    darkPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    darkPalette.setColor(QtGui.QPalette.Light, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.Midlight, QtGui.QColor(90, 90, 90))
    darkPalette.setColor(QtGui.QPalette.Dark, QtGui.QColor(35, 35, 35))
    darkPalette.setColor(QtGui.QPalette.Text, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 42, 42))
    darkPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(BACKGROUND_COLOR))
    darkPalette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(20, 20, 20))
    darkPalette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    darkPalette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.Link, QtGui.QColor(56, 252, 196))
    darkPalette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(66, 66, 66))
    darkPalette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(53, 53, 53))
    darkPalette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor(80, 80, 80))

    # disabled
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText,
                         QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text,
                         QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText,
                         QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight,
                         QtGui.QColor(80, 80, 80))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText,
                         QtGui.QColor(127, 127, 127))

    app.setPalette(darkPalette)

    return app