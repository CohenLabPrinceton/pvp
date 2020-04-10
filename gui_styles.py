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
box-shadow: 1px 1px 1px #000000;
}}

""".format(slider_width=INDICATOR_WIDTH,
    height=HANDLE_HEIGHT,
           slider_color=SLIDER_COLOR)

DISPLAY_VALUE =  """
QLabel {{ 
    color: {textcolor}; 
    font-size: 72pt;
}}""".format(textcolor=TEXT_COLOR)

DISPLAY_VALUE_ALARM =  """
QLabel { 
    color: #ff0000; 
    font-size: 72pt; 
    font-weight: bold;
}"""

DISPLAY_NAME = """
"""

DISPLAY_UNITS = """
"""

DISPLAY_WIDGET = """
border-bottom: 2px solid white;
"""

TITLE_STYLE = """
font-size: 32pt;
color: {text_color};
text-align: left;
""".format(text_color=TEXT_COLOR)

DIVIDER_COLOR = "#FFFFFF"

