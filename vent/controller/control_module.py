import time
from typing import List
import threading
import numpy as np

from vent.common.message import SensorValues, ControlSetting, Alarm, AlarmSeverity, ControlSettingName

lock = threading.Lock()

class ControlModuleBase:
    # Abstract class for controlling hardware based on settings received
    def __init__(self):

        # Internal Control variables. "SET" indicates that this is set.
        self.SET_PIP = 22         # Target PIP pressure
        self.SET_PIP_TIME = 0.4   # Target time to reach PIP in seconds
        self.SET_PEEP = 5         # Target PEEP pressure
        self.SET_PEEP_TIME = 0.5  # Target time to reach PEEP from PIP plateau
        self.SET_BPM = 15         # Target breaths per minute
        self.SET_I_PHASE = 1.3    # Target duration of inspiratory phase

        # Derived internal control variables - fully defined by numbers above
        self.SET_CYCLE_DURATION = 60 / self.SET_BPM
        self.SET_E_PHASE        = self.SET_CYCLE_DURATION - self.SET_I_PHASE
        self.SET_T_PLATEAU      = self.SET_I_PHASE - self.SET_PIP_TIME
        self.SET_T_PEEP         = self.SET_E_PHASE - self.SET_PEEP_TIME

        # These are measurement values from the last breath cycle.
        self.DATA_PIP = None         # Measured value of PIP
        self.DATA_PIP_TIME = None    # Measured time of reaching PIP plateau
        self.DATA_PEEP = None        # Measured valued of PEEP
        self.DATA_I_PHASE = None     # Measured duration of inspiratory phase
        self.DATA_FIRST_PEEP = None  # Time when PEEP is reached first
        self.DATA_LAST_PEEP = None   # Last time of PEEP - by definition end of breath cycle
        self.DATA_BPM = None         # Measured breathing rate, by definition 60sec / length_of_breath_cycle
        self.DATA_VTE = None         # Maximum air displacement in last breath cycle

        self.sensor_values = None
        self.active_alarms = {}  # dictionary of active alarms
        self.logged_alarms = []  # list of all resolved alarms

        # This is what our machine has controll over:
        self.Qin = 0                 # State of a valve on the inspiratory side
        self.Qout = 0                # State of a valve on the expiratory side

        self.pressure = 0
        self.volume = 0
        self.last_update = time.time()

        # Parameters to keep track of breath-cycle
        self.cycle_start = time.time()
        self.cycle_waveforms = {}  # saves the waveforms to meassure pip, peep etc.
        self.cycle_counter = 0

        # Variable limits to raise alarms, initialized as +- 10% of what the controller initializes
        self.PIP_min = self.SET_PIP * 0.9
        self.PIP_max = self.SET_PIP * 1.1
        self.PIP_lastset = time.time()
        self.PIP_time_min = self.SET_PIP_TIME - 0.2 
        self.PIP_time_max = self.SET_PIP_TIME + 0.2
        self.PIP_time_lastset = time.time()
        self.PEEP_min = self.SET_PEEP * 0.9
        self.PEEP_max = self.SET_PEEP * 1.1
        self.PEEP_lastset = time.time()
        self.bpm_min = self.SET_BPM * 0.9
        self.bpm_max = self.SET_BPM * 1.1
        self.bpm_lastset = time.time()
        self.I_phase_min = self.SET_I_PHASE * 0.9
        self.I_phase_max = self.SET_I_PHASE * 1.1
        self.I_phase_lastset = time.time()

        # Run the start() method as a thread
        self.thread = threading.Thread(target=self.start_mainloop, daemon=True)
        self.loop_counter = 0
        self._running = False
        self.thread.start()

    def test_critical_levels(self, min, max, value, name):
        '''
        This tests whether a variable is within bounds.
        If it is, and an alarm existed, then the "alarm_end_time" is set.
        If it is NOT, a new alarm is generated and appendede to the alarm-list.
        Input:
            min:           minimum value  (e.g. 2)
            max:           maximum value  (e.g. 5)
            value:         test value   (e.g. 3)
            name:          parameter type (e.g. "PIP", "PEEP" etc.)
        '''
        if (value < min) or (value > max):  # If the variable is not within limits
            if name not in self.active_alarms.keys():  # And and alarm for that variable doesn't exist yet -> RAISE ALARM.
                new_alarm = Alarm(alarm_name=name, is_active=True, severity=AlarmSeverity.RED, \
                                  alarm_start_time=time.time(), alarm_end_time=None)
                self.active_alarms[name] = new_alarm
        else:  # Else: if the variable is within bounds,
            if name in self.active_alarms.keys():  # And an alarm exists -> inactivate it.
                old_alarm = self.active_alarms[name]
                old_alarm.alarm_end_time = time.time()
                old_alarm.is_active = False
                self.logged_alarms.append(old_alarm)
                del self.active_alarms[name]

    def update_alarms(self):
        ''' This goes through the last waveform, and updates alarms.'''
        this_cycle = self.cycle_counter

        if this_cycle > 1:  # The first cycle for which we can calculate this is cycle "1".
            data = self.cycle_waveforms[this_cycle - 1]
            phase = data[:, 0]
            pressure = data[:, 1]
            volume = data[:, 2]

            self.DATA_VTE = np.max(volume) - np.min(volume)

            # get the pressure niveau heuristically (much faster than fitting)
            # 20 and 80 percentiles pulled out of my hat.
            self.DATA_PEEP = np.percentile(pressure, 20)
            self.DATA_PIP = np.percentile(pressure, 80)

            # measure time of reaching PIP, and leaving PIP
            self.DATA_PIP_TIME = phase[np.min(np.where(pressure > self.DATA_PIP))]
            self.DATA_I_PHASE = phase[np.max(np.where(pressure > self.DATA_PIP))]

            # and measure the same for PEEP
            self.DATA_FIRST_PEEP = phase[np.min(np.where(np.logical_and(pressure < self.DATA_PEEP, phase > 1)))]
            self.DATA_BPM = 60. / phase[-1]  # 60 sec divided by the duration of last waveform

            self.test_critical_levels(min=self.PIP_min, max=self.PIP_max, value=self.DATA_PIP, name="PIP")
            self.test_critical_levels(min=self.PIP_time_min, max=self.PIP_time_max, value=self.DATA_PIP_TIME, name="PIP_TIME")
            self.test_critical_levels(min=self.PEEP_min, max=self.PEEP_max, value=self.DATA_PEEP, name="PEEP")
            self.test_critical_levels(min=self.bpm_min, max=self.bpm_max, value=self.DATA_BPM, name="BREATHS_PER_MINUTE")
            self.test_critical_levels(min=self.I_phase_min, max=self.I_phase_max, value=self.DATA_I_PHASE, name="I_PHASE")

    def get_sensors(self) -> SensorValues:
        # This will depend on simulation vs. reality
        pass

    def get_alarms(self) -> List[Alarms]:
        # Returns all alarms as a list
        ls = self.logged_alarms
        for alarm_key in self.active_alarms.keys():
            ls.append(self.active_alarms[alarm_key])
        return ls

    def get_active_alarms(self):
        # Returns only the active alarms
        return self.active_alarms

    def get_logged_alarms(self) -> List[Alarms]:
        # Returns only the inactive alarms
        return self.logged_alarms

    def set_control(self, control_setting: ControlSetting):
        # Updates the control settings, and re-calculate the derived control variables 
        if control_setting.name == ControlSettingName.PIP:
            self.SET_PIP = control_setting.value
            self.PIP_min = control_setting.min_value
            self.PIP_max = control_setting.max_value
            self.PIP_lastset = control_setting.timestamp

        elif control_setting.name == ControlSettingName.PIP_TIME:
            self.SET_PIP_time = control_setting.value
            self.PIP_time_min = control_setting.min_value
            self.PIP_time_max = control_setting.max_value
            self.PIP_time_lastset = control_setting.timestamp

        elif control_setting.name == ControlSettingName.PEEP:
            self.SET_PEEP = control_setting.value
            self.PEEP_min = control_setting.min_value
            self.PEEP_max = control_setting.max_value
            self.PEEP_lastset = control_setting.timestamp

        elif control_setting.name == ControlSettingName.BREATHS_PER_MINUTE:
            self.SET_BPM = control_setting.value
            self.bpm_min = control_setting.min_value
            self.bpm_max = control_setting.max_value
            self.bpm_lastset = control_setting.timestamp

        elif control_setting.name == ControlSettingName.INSPIRATION_TIME_SEC:
            self.SET_I_PHASE = control_setting.value
            self.I_phase_min = control_setting.min_value
            self.I_phase_max = control_setting.max_value
            self.I_phase_lastset = control_setting.timestamp

        else:
            raise KeyError("You cannot set the variabe: " + str(control_setting.name))

        self.SET_CYCLE_DURATION = 60 / self.SET_BPM
        self.SET_E_PHASE = self.SET_CYCLE_DURATION - self.SET_I_PHASE
        self.SET_T_PLATEAU = self.SET_I_PHASE - self.SET_PIP_TIME
        self.SET_T_PEEP = self.SET_E_PHASE - self.SET_PEEP_TIME

    def get_control(self, control_setting_name: ControlSettingName) -> ControlSetting:
        ''' Updates the control settings. '''
        if control_setting_name == ControlSettingName.PIP:
            return ControlSetting(control_setting_name,
                                  self.SET_PIP,
                                  self.PIP_min,
                                  self.PIP_max,
                                  self.PIP_lastset)
        elif control_setting_name == ControlSettingName.PIP_TIME:
            return ControlSetting(control_setting_name,
                                  self.SET_PIP_time,
                                  self.PIP_time_min,
                                  self.PIP_time_max,
                                  self.PIP_time_lastset, )
        elif control_setting_name == ControlSettingName.PEEP:
            return ControlSetting(control_setting_name,
                                  self.SET_PEEP,
                                  self.PEEP_min,
                                  self.PEEP_max,
                                  self.PEEP_lastset)
        elif control_setting_name == ControlSettingName.BREATHS_PER_MINUTE:
            return ControlSetting(control_setting_name,
                                  self.SET_BPM,
                                  self.bpm_min,
                                  self.bpm_max,
                                  self.bpm_lastset)
        elif control_setting_name == ControlSettingName.INSPIRATION_TIME_SEC:
            return ControlSetting(control_setting_name,
                                  self.SET_I_PHASE,
                                  self.I_phase_min,
                                  self.I_phase_max,
                                  self.I_phase_lastset)
        else:
            raise KeyError("You cannot set the variabe: " + str(control_setting_name))

    def PID_update(self):
        ''' 
        This instantiates the control algorithms.
        During the breathing cycle, it goes through the four states:
           1) Rise to PIP
           2) Sustain PIP pressure
           3) Quick fall to PEEP
           4) Sustaint PEEP pressure
        Once the cycle is complete, it checks the cycle for any alarms, and starts a new one.
        A record of pressure/volume waveforms is kept in self.cycle_waveforms

        RIGHT NOW THIS IS NOT A PID CONTROLLER!

        '''
        now = time.time()
        cycle_phase = now - self.cycle_start
        time_since_last_update = now - self.last_update
        self.last_update = now

        self.volume += time_since_last_update * ( self.Qin - self.Qout )  # Integrate what has happened within the last few seconds
        # NOTE: As Qin and Qout are set, this is what the controllr believes has happened. NOT A MEASUREMENT, MIGHT NOT BE REALITY!

        if cycle_phase < self.SET_PIP_TIME:  # ADD CONTROL dP/dt
            # to PIP, air in as fast as possible
            self.Qin = 1
            self.Qout = 0
            if self.pressure > self.SET_PIP:
                self.Qin = 0
        elif cycle_phase < self.SET_I_PHASE:  # ADD CONTROL P
            # keep PIP plateau, let air in if below
            self.Qin = 0
            self.Qout = 0
            if self.pressure < self.SET_PIP:
                self.Qin = 1
        elif cycle_phase < self.SET_PEEP_TIME + self.SET_I_PHASE:
            # to PEEP, open exit valve
            self.Qin = 0
            self.Qout = 1
            if self.pressure < self.SET_PEEP:
                self.Qout = 0
        elif cycle_phase < self.SET_CYCLE_DURATION:
            # keeping PEEP, let air in if below
            self.Qin = 0
            self.Qout = 0
            if self.pressure < self.SET_PEEP:
                self.Qin = 1
        else:
            self.cycle_start = time.time()  # new cycle starts
            self.cycle_counter += 1
            self.update_alarms()            # Run alarm detection over last cycle's waveform
            
        if self.cycle_counter not in self.cycle_waveforms.keys():  # if this cycle doesn't exist yet, start it
            self.cycle_waveforms[self.cycle_counter] = np.array([[0, self.pressure, self.volume]])  # add volume
        else:
            data = self.cycle_waveforms[self.cycle_counter]
            data = np.append(data, [[cycle_phase, self.pressure, self.volume]], axis=0)
            self.cycle_waveforms[self.cycle_counter] = data

    def start_mainloop(self):
        # This will depend on simulation or reality
        pass   

    def start(self):
        if not self.thread.is_alive():  # If the previous thread has been stopped, make a new one.
            self._running = True
            self.thread = threading.Thread(target=self.start_mainloop, daemon=True)
            self.thread.start()
        else:
            print("Main Loop already running.")

    def stop(self):
        if self.thread.is_alive():
            self._running = False
        else:
            print("Main Loop is not running.")



class ControlModuleDevice(ControlModuleBase):
    # Implement ControlModuleBase functions
    pass




class Balloon_Simulator:
    '''
    This is a imple physics simulator for inflating a balloon. 
    For math, see https://en.wikipedia.org/wiki/Two-balloon_experiment
    '''

    def __init__(self, leak, delay):
        # Hard parameters for the simulation
        self.max_volume = 6  # Liters  - 6?
        self.min_volume = 1.5  # Liters - baloon starts slightly inflated.
        self.PC = 20  # Proportionality constant that relates pressure to cm-H2O
        self.P0 = 0  # Minimum pressure.
        self.leak = leak
        self.delay = delay

        self.temperature = 37  # keep track of this, as is important output variable
        self.humidity = 90
        self.fio2 = 60

        # Dynamical parameters - these are the initial conditions
        self.current_flow = 0  # in unit  liters/sec
        self.current_pressure = 0  # in unit  cm-H2O
        self.r_real = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)  # size of the lung
        self.current_volume = self.min_volume  # in unit  liters

    def get_pressure(self):
        return self.current_pressure

    def get_volume(self):
        return self.current_volume

    def set_flow(self, Qin, Qout):
        self.current_flow = Qin - Qout

    def update(self, dt):  # Performs an update of duration dt [seconds]
        self.current_volume += self.current_flow * dt

        if self.leak:
            RC = 5  # pulled 5 sec out of my hat
            s = dt / (RC + dt)
            self.current_volume = self.current_volume + s * (self.min_volume - self.current_volume)

        # This is fromt the baloon equation, uses helper variable (the baloon radius)
        r_target = (3 * self.current_volume / (4 * np.pi)) ** (1 / 3)
        r0 = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)

        # Delay -> Expansion takes time
        if self.delay:
            RC = 0.1  # pulled these 100ms out of my hat
            s = dt / (RC + dt)
            self.r_real = self.r_real + s * (r_target - self.r_real)
        else:
            self.r_real = r_target

        self.current_pressure = self.P0 + (self.PC / (r0 ** 2 * self.r_real)) * (1 - (r0 / self.r_real) ** 6)

        # Temperature, humidity and o2 fluctuations modelled as OUprocess
        self.temperature = self.OUupdate(self.temperature, dt=dt, mu=37, sigma=0.3, tau=1)
        self.fio2 = self.OUupdate(self.fio2, dt=dt, mu=60, sigma=5, tau=1)
        self.humidity = self.OUupdate(self.humidity, dt=dt, mu=90, sigma=5, tau=1)
        if self.humidity > 100:
            self.humidity = 100

    def OUupdate(self, variable, dt, mu, sigma, tau):
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

class ControlModuleSimulator(ControlModuleBase):
    # Implement ControlModuleBase functions
    def __init__(self):
        ControlModuleBase.__init__(self)

        self.Balloon = Balloon_Simulator(leak=True, delay=False)          # SIMULATION

    def get_sensors(self):
        # returns SensorValues and a time stamp
        lock.acquire()
        self.sensor_values = SensorValues(pip=self.DATA_PIP,
                                          peep=self.DATA_PEEP,
                                          fio2=self.Balloon.fio2,
                                          temp=self.Balloon.temperature,
                                          humidity=self.Balloon.humidity,
                                          pressure=self.Balloon.current_pressure,
                                          vte=self.DATA_VTE,
                                          breaths_per_minute=self.DATA_BPM,
                                          inspiration_time_sec=self.DATA_I_PHASE,
                                          timestamp=time.time(),
                                          loop_counter = self.loop_counter)
        lock.release()
        return self.sensor_values

    def start_mainloop(self):
        # start running
        # this should be run as a thread! 
        # Compare to initialization

        while self._running:
            time.sleep(.01)
            self.loop_counter += 1
            now = time.time()

            # Only one sensor "is connected" and that is the pressure in the balloon
            self.Balloon.update(now - self.last_update)
            self.last_update = now
            self.pressure = self.Balloon.get_pressure()

            self.PID_update()

            self.Balloon.set_flow(self.Qin, self.Qout)

    def heartbeat(self):
        '''only used for fiddling'''
        if self._running:
            print("Controller running...")
        else:
            print("Controller not running...")
        print("Current loop = " + str(self.loop_counter)+'.\n')




def get_control_module(sim_mode=False):
    if sim_mode == True:
        return ControlModuleSimulator()
    else:
        return ControlModuleDevice()
