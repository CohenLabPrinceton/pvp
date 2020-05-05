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
HANDLE_HEIGHT = 10
SLIDER_WIDTH = 80
INDICATOR_WIDTH = SLIDER_WIDTH/3
SLIDER_COLOR = TEXT_COLOR
INDICATOR_COLOR = SUBWAY_COLORS['blue']
ALARM_COLOR = "#FF0000"

VALUE_SIZE = 72
NAME_SIZE = 20
UNIT_SIZE = 12

GLOBAL = """
QWidget {{
    font-size: 20pt;
    color: {textcolor};
}}
""".format(textcolor=TEXT_COLOR)

RANGE_SLIDER = """
QSlider {{
    font-size: 12px;
}}
QSlider::groove:vertical {{
border: 1px solid #FFFFFF;
width: {slider_width}px;
}}
QSlider::handle:vertical {{
height: {height}px;
width: 20px;
margin: 0px -20px 0px px;
background-color: {slider_color};
}}

""".format(slider_width=INDICATOR_WIDTH,
    height=HANDLE_HEIGHT,
           slider_color=SLIDER_COLOR)



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