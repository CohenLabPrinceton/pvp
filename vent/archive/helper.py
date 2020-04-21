# This Python file contains helper functions. 

def clamp(value):
    # Clamps values within range (0, 1)
    return max(min(1, value), 0)
