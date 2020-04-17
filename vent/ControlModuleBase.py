class ControlModuleBase:
    # Abstract class for controlling hardware based on settings received
    #   Functions:
    def __init__(self):
        self.sensor_values = None
        self.control_settings = None
        self.loop_counter = None

    def get_sensors_values(self):
        # returns SensorValues
        # include a timestamp and loop counter
        pass

    def get_alarms(self):
        pass

    def set_controls(self, controlSettings):
        pass

    def start(self, controlSettings):
        # start running
        # controls actuators to achieve target state
        # determined by settings and assessed by sensor values
        pass

    def stop(self):
        # stop running
        pass


# Variables:
#   sensorValues
#   controlSettings
#   loopCounter

class ControlModuleDevice(ControlModuleBase):
    # Implement ControlModuleBase functions
    pass


class ControlModuleSimulator(ControlModuleBase):
    # Implement ControlModuleBase functions
    def __init__(self, fname, lname, year):
        super().__init__(fname, lname)      # get all from parent

        self.Balloon = Balloon_Simulator(leak = False, delay = False)
        self.Controller = StateController()

    def get_sensors_values(self):
        # returns SensorValues
        # include a timestamp and loop counter
        pressure = Patient.get_pressure()
        self.sensor_values = FORMAT(...) 
        return (self.timestamp, self.loop_counter)



    def get_alarms(self):
        return 1

    def set_controls(self, controlSettings):
        # set PIP, PEEP...
        pass

    def start(self, controlSettings):
        # start running
        # controls actuators to achieve target state
        # determined by settings and assessed by sensor values

        while true:
            time.sleep(0.01)
            self.loop_counter += 1
            Controller.update(self.pressure)
            Qout = Controller.get_Qout()
            Qin  = Controller.get_Qin()

            Patient.set_flow(Qin, Qout)
        
        pass
    def stop(self):
        # stop running
        pass

def get_control_module(sim_mode=False):
    if sim_mode == True:
        return ControlModuleSimulator()
    else:
        return ControlModuleDevice()