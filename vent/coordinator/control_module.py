import numpy as np
import time
from typing import List
from .common.message import SensorValues, ControlSettings, Alarm, AlarmSeverity, ControlSettingName

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
    This is a class to control a respirator by iterating through set states with hard-coded valve settings
    '''
    def __init__(self):
        self.PIP              = 22
        self.PIP_time         = 1.0
        self.PEEP             = 5
        self.PEEP_time        = 0.5    # as fast as possible, try 500ms
        self.bpm              = 10
        self.I_phase          = 1.0
        self.Qin              = 0
        self.Qout             = 0
        self.pressure         = 0

        #Derived variables
        self.cycle_duration   = 60/self.bpm
        self.E_phase          = self.cycle_duration -  self.I_phase
        self.t_inspiration    = self.PIP_time   # time [sec] for the four phases
        self.t_plateau        = self.I_phase - self.PIP_time 
        self.t_expiration     = self.PEEP_time 
        self.t_PEEP           = self.E_phase - self.PEEP_time 

        # Parameters to keep track of breath-cycle
        self.cycle_start      = time.time()
        self.cycle_pressure_waveforms  = {}    # saves the waveforms to meassure pip, peep etc.
        self.cycle_counter    = 0

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
            self.cycle_start    = time.time() # new cycle starts
            self.cycle_counter += 1

        if self.cycle_counter not in self.cycle_pressure_waveforms.keys():   #if this cycle doesn't exist yet, start it
            self.cycle_pressure_waveforms[self.cycle_counter] = np.array([[0, pressure]])
        else:
            data = self.cycle_pressure_waveforms[self.cycle_counter]
            data = np.append(data, [[cycle_phase, pressure]], axis=0)
            self.cycle_pressure_waveforms[self.cycle_counter] = data


def test_critical_levels(min, max, value, name, active_alarms, logged_alarms):
    '''
    This tests whether a variable is within bounds.
    If it is, and an alarm existed, then the "alarm_end_time" is set.
    If it is NOT, a new alarm is generated and appendede to the alarm-list.
    Input:
        min:           minimum value  (e.g. 2)
        max:           maximum value  (e.g. 5)
        value:         test value   (e.g. 3)
        name:          parameter type (e.g. "PIP", "PEEP" etc.)
        active_alarms: dictionary of active alarms
        logged_alarms: list of the logged alarms
    Returns:
        alarms: updated active_alarms and logged_alarms

    '''
    if (value<min) or (value>max):                 # If the variable is not within limits
        if name not in active_alarms.keys():       # And and alarm for that variable doesn't exist yet -> RAISE ALARM.
            new_alarm = Alarm(alarm_name = name, is_active = True, severity = AlarmSeverity.RED, \
                              alarm_start_time = time.time(), alarm_end_time = None)
            active_alarms[name] = new_alarm
            # print(str(name) + ": " + str(min) + " < " + str(value) + " < " + str(max) + "  violated.")

    else:                                          # Else: if the variable is within bounds, 
        if name in active_alarms.keys():           # And an alarm exists -> inactivate it.
            old_alarm = active_alarms[name]
            old_alarm.alarm_end_time = time.time()
            old_alarm.is_active      = False
            logged_alarms.append( old_alarm )
            del active_alarms[name]

    return active_alarms, logged_alarms


class ControlModuleSimulator(ControlModuleBase):
    # Implement ControlModuleBase functions
    def __init__(self):
        super().__init__()      # get all from parent

        self.Balloon = Balloon_Simulator(leak = True, delay = False)
        self.Controller = StateController()
        self.loop_counter = 0
        self.pressure = 15
        self.last_update = time.time()

        # Variable limits to raise alarms, initialized as +- 10% of what the controller initializes
        self.PIP_min          = self.Controller.PIP      *0.9
        self.PIP_max          = self.Controller.PIP      *1.1
        self.PIP_lastset      = time.time()
        self.PIP_time_min     = self.Controller.PIP_time *0.9
        self.PIP_time_max     = self.Controller.PIP_time *1.1
        self.PIP_time_lastset = time.time()
        self.PEEP_min         = self.Controller.PEEP     *0.9
        self.PEEP_max         = self.Controller.PEEP     *1.1
        self.PEEP_lastset     = time.time()
        self.bpm_min          = self.Controller.bpm      *0.9
        self.bpm_max          = self.Controller.bpm      *1.1
        self.bpm_lastset      = time.time()
        self.I_phase_min      = self.Controller.I_phase  *0.9
        self.I_phase_max      = self.Controller.I_phase  *1.1
        self.I_phase_lastset  = time.time()

        # Alarm management
        self.active_alarms           = {}    # dictionary of active alarms
        self.logged_alarms           = []    # list of all resolved alarms 

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


    def update_alarms(self):
        ''' This goes through the LAST waveform, and updates alarms.'''
        this_cycle = self.Controller.cycle_counter

        if this_cycle > 1:   #The first cycle for which we can calculate this is cycle "1".
            data = self.Controller.cycle_pressure_waveforms[this_cycle-1]
            phase = data[:,0]
            pressure = data[:,1]

            # get the pressure niveau heuristically (much faster than fitting)
            # 20 and 80 percentiles pulled out of my hat.
            PEEP = np.percentile(pressure,20)
            PIP  = np.percentile(pressure,80)

            # measure time of reaching PIP, and leaving PIP
            last_PIP   = phase[ np.max(np.where(pressure>PIP)) ]
            first_PIP  = phase[ np.min(np.where(pressure>PIP)) ]
            # and measure the same for PEEP
            first_PEEP = phase[ np.min(np.where(np.logical_and(pressure<PEEP, phase > 1))) ]
            last_PEEP  = phase[-1]

            bpm     = 60./last_PEEP  # 60 sec divided by the duration of last waveform
            I_phase = last_PIP       # last time-point of the plateau
            
            self.active_alarms, self.logged_alarms = test_critical_levels(min = self.PIP_min,      max = self.PIP_max,      value = PIP,       \
                                            name = "PIP",                active_alarms = self.active_alarms,    logged_alarms = self.logged_alarms)
            self.active_alarms, self.logged_alarms = test_critical_levels(min = self.PIP_time_min, max = self.PIP_time_max, value = first_PIP, \
                                            name = "PIP_TIME",           active_alarms = self.active_alarms,    logged_alarms = self.logged_alarms)
            self.active_alarms, self.logged_alarms = test_critical_levels(min = self.PEEP_min,     max = self.PEEP_max,     value = PEEP,      \
                                            name = "PEEP",               active_alarms = self.active_alarms,    logged_alarms = self.logged_alarms)
            self.active_alarms, self.logged_alarms = test_critical_levels(min = self.bpm_min,      max = self.bpm_max,      value = bpm,       \
                                            name = "BREATHS_PER_MINUTE", active_alarms = self.active_alarms,    logged_alarms = self.logged_alarms)
            self.active_alarms, self.logged_alarms = test_critical_levels(min = self.I_phase_min,  max = self.I_phase_max,  value = I_phase,   \
                                            name = "I_PHASE",            active_alarms = self.active_alarms,    logged_alarms = self.logged_alarms)

    def get_alarms(self):
        #Returns all alarms as a list
        ls = self.logged_alarms
        for alarm_key in self.active_alarms.keys():
            ls.append( self.active_alarms[alarm_key] )
        return ls

    def get_active_alarms(self):
        #Returns only the active alarms
        return self.active_alarms
        
    def get_logged_alarms(self):
        #Returns only the inactive alarms
        return self.logged_alarms

    def set_controls(self, controlSettings):
        ''' Updates the control settings. '''
        if controlSettings.name is ControlSettingName.PIP:
            self.Controller.PIP      = controlSettings.value 
            self.PIP_min             = controlSettings.min_value
            self.PIP_max             = controlSettings.max_value
            self.PIP_lastset         = controlSettings.timestamp

        elif controlSettings.name is ControlSettingName.PIP_TIME:
            self.Controller.PIP_time = controlSettings.value
            self.PIP_time_min        = controlSettings.min_value
            self.PIP_time_max        = controlSettings.max_value
            self.PIP_time_lastset    = controlSettings.timestamp

        elif controlSettings.name is ControlSettingName.PEEP:
            self.Controller.PEEP      = controlSettings.value
            self.PEEP_min            = controlSettings.min_value
            self.PEEP_max            = controlSettings.max_value
            self.PEEP_lastset        = controlSettings.timestamp

        elif controlSettings.name is ControlSettingName.BREATHS_PER_MINUTE:
            self.Controller.bpm      = controlSettings.value
            self.bpm_min             = controlSettings.min_value
            self.bpm_max             = controlSettings.max_value
            self.bpm_lastset         = controlSettings.timestamp

        elif controlSettings.name is ControlSettingName.INSPIRATION_TIME_SEC:
            self.Controller.I_phase  = controlSettings.value
            self.I_phase_min         = controlSettings.min_value
            self.I_phase_max         = controlSettings.max_value
            self.I_phase_lastset     = controlSettings.timestamp

        else:
            error("You cannot set the variabe: " + str(controlSettings.name))

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

        # Would be nice to check for alarms here, on every breath cycle.

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



