class HALMock():
    """ A HAL mock class to fall back to, if io.HAL times out. 
    Only thing it does is storing the communication variables.
    """
    def __init__(self):
        self.setpoint_in = 0
        self.setpoint_ex = 0
        self.pressure    = 0
        self.oxygen      = 0
        self.flow_ex     = 0