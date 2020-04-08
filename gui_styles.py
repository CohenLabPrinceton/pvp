BACKGROUND_COLOR = "#111111"
TEXT_COLOR = "#EEEEEE"

GLOBAL = """
QWidget {{
    font-size: 20pt;
    color: {textcolor};
}}
""".format(textcolor=TEXT_COLOR)

RANGE_SLIDER = """


"""

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