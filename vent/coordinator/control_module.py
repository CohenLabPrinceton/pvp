import numpy as np
import threading
import time
from typing import List
from .common.message import SensorValues, ControlSettings, Alarm, ControlSettingName

class ControlModuleBase:
    # Abstract class for controlling hardware based on settings received
    #   Functions:
    def __init__(self):
        self.sensor_values = None
        self.control_settings = None
        self.loop_counter = None

    def get_sensors(self) -> SensorValues:
        # returns SensorValues
        # include a timestamp and loop counter
        pass

    def get_active_alarms(self) -> List[Alarm]:
        pass

    def get_logged_alarms(self) -> List[Alarm]:
        pass

    def clear_logged_alarms(self):
        pass

    def set_controls(self, control_settings: ControlSettings):
        # takes ControlSettings struct
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
#   controlSettings.  
#   loopCounter

class ControlModuleDevice(ControlModuleBase):
    # Implement ControlModuleBase functions
    pass



class Balloon_Simulator:
    '''
    This is a simulator for inflating a balloon. 
    For math, see https://en.wikipedia.org/wiki/Two-balloon_experiment
    '''
    
    def __init__(self, leak, delay):
        #Hard parameters for the simulation
        self.max_volume       = 6     # Liters  - 6?
        self.min_volume       = 1.5   # Liters - baloon starts slightly inflated.
        self.PC               = 20    # Proportionality constant that relates pressure to cm-H2O 
        self.P0               = 0     # Minimum pressure.
        self.leak             = leak
        self.delay            = delay

        self.temperature      = 37   # keep track of this, as is important output variable
        self.humidity         = 90
        self.fio2             = 60

        #Dynamical parameters - these are the initial conditions
        self.current_flow     = 0                  # in unit  liters/sec
        self.current_pressure = 0                  # in unit  cm-H2O
        self.r_real           = (3*self.min_volume / (4*np.pi))**(1/3)                  # size of the lung
        self.current_volume   = self.min_volume    # in unit  liters
    
    def get_pressure(self):
        return self.current_pressure
    def get_volume(self):
        return self.current_volume
    def set_flow(self, Qin, Qout):
        self.current_flow = Qin-Qout
        
    def update(self, dt):   # Performs an update of duration dt [seconds]
        self.current_volume += self.current_flow*dt
        
        if self.leak:
            RC = 5  # pulled 5 sec out of my hat
            s = dt / (RC + dt)
            self.current_volume = self.current_volume + s * (self.min_volume - self.current_volume)
        
        #This is fromt the baloon equation, uses helper variable (the baloon radius)
        r_target  = (3*self.current_volume / (4*np.pi))**(1/3)
        r0 = (3*self.min_volume / (4*np.pi))**(1/3)
        
        #Delay -> Expansion takes time
        if self.delay:
            RC = 0.1  # pulled these 100ms out of my hat
            s = dt / (RC + dt)
            self.r_real = self.r_real + s * (r_target - self.r_real)
        else:
            self.r_real = r_target
            
        self.current_pressure = self.P0 + (self.PC/(r0**2 * self.r_real)) *(1 - (r0/self.r_real)**6)

        #Temperature, humidity and o2 fluctuations modelled as OUprocess
        self.temperature = OUupdate(self.temperature, dt=dt, mu=37, sigma=0.3, tau=1)
        self.fio2        = OUupdate(self.fio2,        dt=dt, mu=60, sigma=5,   tau=1)
        self.humidity    = OUupdate(self.humidity,    dt=dt, mu=90, sigma=5,   tau=1)
        if self.humidity>100:
            self.humidity = 100

def OUupdate(variable, dt, mu, sigma, tau):
    '''
    This is a simple function to produce an OU process.
    It is used as model for fluctuations in measurement variables.
    inputs:
       variable:   float     value at previous time step
       dt      :   timestep
       mu      :   mean
       sigma   :   noise amplitude
       tau     :   time scale
    returns:
       new_variable :  value of "variable" at next time step
    '''
    sigma_bis = sigma * np.sqrt(2. / tau)
    sqrtdt = np.sqrt(dt)
    new_variable = variable + dt * (-(variable - mu) / tau) + sigma_bis * sqrtdt * np.random.randn()
    return new_variable

class StateController:
    '''
    This is a class to control a respirator by iterating through set states.
    Inspiration:
        Start timer
        Open insp. valve
        Close expire valve
        Poll pressure sensor - press>PIP?
    
    Plateau:
        Close insp valve
        poll timer
        long enough? expiration
        
    Expiration:
        Open expir. valve
        poll pressure sensor
        Pressure<PEEP?
        maintain PEEP
        
    PEEP:
        Close expiration valve
        poll timer
        breath long enough
        set state to inspiration.
        
    '''
    def __init__(self):
        self.PIP            = 22
        self.PIP_time       = 1.0
        self.PEEP           = 5
        self.PEEP_time      = 0.5    # as fast as possible, try 500ms
        self.bpm            = 10
        self.I_phase        = 1.0
        self.cycle_start    = time.time()
        self.Qin            = 0
        self.Qout           = 0
        self.pressure       = 0

        #Derived variables
        self.cycle_duration = 60/self.bpm
        self.E_phase        = self.cycle_duration -  self.I_phase
        self.t_inspiration  = self.PIP_time   # time [sec] for the four phases
        self.t_plateau      = self.I_phase - self.PIP_time 
        self.t_expiration   = self.PEEP_time 
        self.t_PEEP         = self.E_phase - self.PEEP_time 

    def update_internalVeriables(self):
        self.cycle_duration = 60/self.bpm
        self.E_phase        = self.cycle_duration -  self.I_phase
        self.t_inspiration  = self.PIP_time
        self.t_plateau      = self.I_phase - self.PIP_time 
        self.t_expiration   = self.PEEP_time 
        self.t_PEEP         = self.E_phase - self.PEEP_time 
        
    def get_Qin(self):
        return self.Qin
    
    def get_Qout(self):
        return self.Qout
    
    def update(self, pressure):
        now = time.time()
        cycle_phase = now - self.cycle_start

        self.pressure = pressure
        if cycle_phase < self.t_inspiration:       # ADD CONTROL dP/dt
            # to PIP, air in as fast as possible
            self.Qin  = 1
            self.Qout = 0  
            if self.pressure > self.PIP:
                self.Qin = 0
        elif cycle_phase < self.I_phase:           # ADD CONTROL P
            # keep PIP plateau, let air in if below
            self.Qin  = 0
            self.Qout = 0
            if self.pressure < self.PIP:
                self.Qin = 1
        elif cycle_phase < self.t_expiration + self.I_phase:
            # to PEEP, open exit valve
            self.Qin  = 0
            self.Qout = 1
            if self.pressure < self.PEEP:
                self.Qout = 0
        elif cycle_phase < self.cycle_duration:
            # keeping PEEP, let air in if below
            self.Qin  = 0
            self.Qout = 0
            if self.pressure < self.PEEP:
                self.Qin = 1
        else:
            self.cycle_start = time.time() # restart



class ControlModuleSimulator(ControlModuleBase):
    # Implement ControlModuleBase functions
    def __init__(self):
        super().__init__()      # get all from parent

        self.Balloon = Balloon_Simulator(leak = True, delay = False)
        self.Controller = StateController()
        self.loop_counter = 0
        self.pressure = 15
        self.last_update = time.time()

    def get_sensors_values(self):
        # returns SensorValues and a time stamp

        ExhaledVolumeLastCycle = np.nan             # FIX THIS

        self.sensor_values = SensorValues(pip = self.Controller.PIP, \
            peep = self.Controller.PEEP,                             \
            fio2 = self.Balloon.fio2,                                \
            temp = self.Balloon.temperature,                         \
            humidity = self.Balloon.humidity,                        \
            pressure = self.Balloon.current_pressure,                \
            vte = ExhaledVolumeLastCycle,                            \
            breaths_per_minute = self.Controller.bpm,                \
            inspiration_time_sec = self.Controller.I_phase,          \
            timestamp = time.time() )

        return self.sensor_values


    def get_alarms(self):
        return 1

    def set_controls(self, controlSettings):
        #Right now, this supports only five settings
        if controlSettings.name is ControlSettingName.PIP:
            self.Controller.PIP = controlSettings.value 

        elif controlSettings.name is ControlSettingName.PIP_TIME:
            self.Controller.PIP_time = controlSettings.value

        elif controlSettings.name is ControlSettingName.PEEP:
            self.Controller.PEEP = controlSettings.value

        elif controlSettings.name is ControlSettingName.BREATHS_PER_MINUTE:
            self.Controller.bpm = controlSettings.value

        elif controlSettings.name is ControlSettingName.INSPIRATION_TIME_SEC:
            self.Controller.I_phase = controlSettings.value

        else:
            error("you cannot set" + str(controlSettings.name))

        self.Controller.update_internalVeriables()
        
    def run(self):
        # start running
        # controls actuators to achieve target state
        # determined by settings and assessed by sensor values


        self.loop_counter += 1
        now = time.time()
        self.Balloon.update(now - self.last_update)
        self.last_update = now

        pressure = self.Balloon.get_pressure()
        temperature = self.Balloon.temperature

        self.Controller.update(pressure)
        Qout = self.Controller.get_Qout()
        Qin  = self.Controller.get_Qin()
        self.Balloon.set_flow(Qin, Qout)

    def stop(self):
        # stop running
        pass

    def recvUIHeartbeat(self):
        return time.time()


def get_control_module(sim_mode=False):
    if sim_mode == True:
        return ControlModuleSimulator()
    else:
        return ControlModuleDevice()


class ControllerThread(threading.Thread):
    """
    Copied & Pasted from /sandbox/testPIDControllerClass
    -jls 042020

    """
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.ContollInstance = get_control_module(sim_mode=True)

    def run(self):
        while self.counter:
            #     controls actuators to achieve target state
            self.ContollInstance.run()  # run a contol update
            time.sleep(.01)  # wait 10ms
            self.counter -= 1

    def set_controls(self, command):
        self.ContollInstance.set_controls(command)

    def get_sensor_values(self):
        # returns SensorValues, include a timestamp and loop counter
        sv = self.ContollInstance.get_sensors_values()
        sv.loop_counter = self.counter
        return sv

    def heartbeat(self):
        print("%s: %s" % (self.name, time.ctime(time.time())))
        print("Internal counter =" + str(self.counter) + '.\n')

