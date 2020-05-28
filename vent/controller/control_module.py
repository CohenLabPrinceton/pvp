import time
from typing import List
import threading
import numpy as np
import copy
from collections import deque
import pdb
from itertools import count

import vent.io as io

from vent.common.message import SensorValues, ControlSetting
from vent.common.logging import init_logger
from vent.common.values import CONTROL, ValueName
from vent.alarm import AlarmSeverity, Alarm



class ControlModuleBase:
    """This is an abstract class for controlling simulation and hardware.

    1. All internal variables fall in three classes, denoted by the beginning of the variable:
        - "COPY_varname": These are copies (see 1.) that are regularly sync'ed with internal variables.
        - "__varname":    These are variables only used in the ControlModuleBase-Class
        - "_varname":     These are variables used in derived classes.

    2. Internal variables should only to be accessed though the set_ and get_ functions.
        These functions act on COPIES of internal variables ("__" and "_"), that are sync'd every few
        iterations. How often this is done is adjusted by the variable
        self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE. To avoid multiple threads manipulating the same 
        variables at the same time, every manipulation of "COPY_" is surrounded by a thread lock.

    Public Methods:
        get_sensors():                     Returns a copy of the current sensor values.
        get_alarms():                      Returns a List of all alarms, active and logged
        get_active_alarms():               Returns a Dictionary of all currently active alarms.
        get_logged_alarms():               Returns a List of logged alarms, up to maximum lengh of self._RINGBUFFER_SIZE
        get_control(ControlSetting):       Sets a controll-setting. Is updated at latest within self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
        get_past_waveforms():              Returns a List of waveforms of pressure and volume during at the last N breath cycles, N<self._RINGBUFFER_SIZE, AND clears this archive.
        get_target_waveform():             Returns a step-wise linear target waveform, as defined by the current settings.
        start():                           Starts the main-loop of the controller
        stop():                            Stops the main-loop of the controller

    """

    def __init__(self):
        self.logger = init_logger(__name__)
        self.logger.info('controller init')
        #####################  Algorithm/Program parameters  ##################
        # Hyper-Parameters
        self._LOOP_UPDATE_TIME                   = 0.01    # Run the main control loop every 0.01 sec
        self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE = 10      # After every 10 main control loop iterations, update COPYs.
        self._RINGBUFFER_SIZE                    = 100     # Maximum number of breath cycles kept in memory

        #########################  Control management  #########################

        # This is what the machine has controll over:
        self.__control_signal_in  = 0              # State of a valve on the inspiratory side - could be a proportional valve.
        self.__control_signal_out = 0              # State of a valve on the exspiratory side - this is open/close i.e. value in (0,1)
        self._pid_control_flag    = True           # Default is: use PID control
        self.__KP                 = 80             # The weights for the the PID terms
        self.__KI                 = 0
        self.__KD                 = 0


        # Internal Control variables. "SET" indicates that this is set.
        self.__SET_PIP       = CONTROL[ValueName.PIP].default                     # Target PIP pressure
        self.__SET_PIP_TIME  = CONTROL[ValueName.PIP_TIME].default                # Target time to reach PIP in seconds
        self.__SET_PEEP      = CONTROL[ValueName.PEEP].default                    # Target PEEP pressure
        self.__SET_PEEP_TIME = CONTROL[ValueName.PEEP_TIME].default               # Target time to reach PEEP from PIP plateau
        self.__SET_BPM       = CONTROL[ValueName.BREATHS_PER_MINUTE].default      # Target breaths per minute
        self.__SET_I_PHASE   = CONTROL[ValueName.INSPIRATION_TIME_SEC].default    # Target duration of inspiratory phase

        # Derived internal control variables - fully defined by numbers above
        self.__SET_CYCLE_DURATION = 60 / self.__SET_BPM
        self.__SET_E_PHASE        = self.__SET_CYCLE_DURATION - self.__SET_I_PHASE
        self.__SET_T_PLATEAU      = self.__SET_I_PHASE - self.__SET_PIP_TIME
        self.__SET_T_PEEP         = self.__SET_E_PHASE - self.__SET_PEEP_TIME

        #########################  Data management  #########################

        # These are measurements from the last breath cycle.
        self._DATA_PIP = None         # Measured value of PIP
        self._DATA_PIP_PLATEAU = None # Measured pressure of the plateau
        self._DATA_PIP_TIME = None    # Measured time of reaching PIP plateau
        self._DATA_PEEP = None        # Measured valued of PEEP
        self._DATA_I_PHASE = None     # Measured duration of inspiratory phase
        self.__DATA_LAST_PEEP = None  # Last time of PEEP - by definition end of breath cycle
        self._DATA_BPM = None         # Measured breathing rate, by definition 60sec / length_of_breath_cycle
        self._DATA_VTE = None         # Maximum air displacement in last breath cycle
        self._DATA_P = 0              # Last measurements of the proportional term for PID-control
        self._DATA_I = 0              # Last measurements of the integral term for PID-control
        self._DATA_D = 0              # Last measurements of the differential term for PID-control
        self._DATA_BREATH_COUNT = 0   # Total number of breaths/id of current breath cycle
        self._breath_counter = count() # threadsafe counter

        # Parameters to keep track of breath-cycle
        self.__cycle_start = time.time()
        self.__cycle_waveform = np.array([[0, 0, 0]])                            # To build up the current cycle's waveform
        self.__cycle_waveform_archive = deque(maxlen = self._RINGBUFFER_SIZE)          # An archive of past waveforms.

        # These are measurements that change from timepoint to timepoint
        self._DATA_PRESSURE = 0
        self.__DATA_VOLUME  = 0
        self._DATA_Qin      = 0           # Measurement of the airflow in
        self._DATA_Qout     = 0           # Measurement of the airflow out
        self._DATA_dpdt     = 0           # Current sample of the rate of change of pressure dP/dt in cmH2O/sec
        self._last_update   = time.time()


        #########################  Alarm management  #########################
        self.__active_alarms = {}     # Dictionary of active alarms
        self.__logged_alarms = deque(maxlen = self._RINGBUFFER_SIZE)     # List of all resolved alarms

        # Variable limits to raise alarms, initialized as small deviation of what the controller initializes
        self.__PIP_min          = CONTROL[ValueName.PIP].safe_range[0]
        self.__PIP_max          = CONTROL[ValueName.PIP].safe_range[1]
        self.__PIP_lastset      = time.time()
        self.__PIP_time_min     = CONTROL[ValueName.PIP_TIME].safe_range[0]
        self.__PIP_time_max     = CONTROL[ValueName.PIP_TIME].safe_range[1]
        self.__PIP_time_lastset = time.time()
        self.__PEEP_min         = CONTROL[ValueName.PEEP].safe_range[0]
        self.__PEEP_max         = CONTROL[ValueName.PEEP].safe_range[1]
        self.__PEEP_lastset     = time.time()
        self.__PEEP_time_min    = CONTROL[ValueName.PEEP_TIME].safe_range[0]
        self.__PEEP_time_max    = CONTROL[ValueName.PEEP_TIME].safe_range[1]
        self.__PEEP_time_lastset = time.time()
        self.__bpm_min          = CONTROL[ValueName.BREATHS_PER_MINUTE].safe_range[0]
        self.__bpm_max          = CONTROL[ValueName.BREATHS_PER_MINUTE].safe_range[1]
        self.__bpm_lastset      = time.time()
        self.__I_phase_min      = CONTROL[ValueName.INSPIRATION_TIME_SEC].safe_range[0]
        self.__I_phase_max      = CONTROL[ValueName.INSPIRATION_TIME_SEC].safe_range[1]
        self.__I_phase_lastset  = time.time()

        ############### Initialize COPY variables for threads  ##############
        # COPY variables that later updated on a regular basis
        self.COPY_active_alarms = {}
        self.COPY_logged_alarms = list(self.__logged_alarms)
        self.COPY_sensor_values = None # empty SensorValues can no longer be instantiated -jls

        ###########################  Threading init  #########################
        # Run the start() method as a thread
        self._loop_counter = 0
        self._running = threading.Event()
        self._running.clear()
        self._lock = threading.Lock()
        self._alarm_to_COPY()  #These require the lock
        self._initialize_set_to_COPY()

        # self.__thread = threading.Thread(target=self._start_mainloop, daemon=True)
        # self.__thread.start()
        self.__thread = None


    def _initialize_set_to_COPY(self):
        self._lock.acquire()
        # Copy of the SET variables for threading.
        self.COPY_SET_PIP       = self.__SET_PIP 
        self.COPY_SET_PIP_TIME  = self.__SET_PIP_TIME
        self.COPY_SET_PEEP      = self.__SET_PEEP
        self.COPY_SET_PEEP_TIME = self.__SET_PEEP_TIME
        self.COPY_SET_BPM       = self.__SET_BPM
        self.COPY_SET_I_PHASE   = self.__SET_I_PHASE
        self._lock.release()

    def _alarm_to_COPY(self):
        self._lock.acquire()
        # Update the alarms
        self.COPY_active_alarms = self.__active_alarms.copy()
        self.COPY_logged_alarms = list(self.__logged_alarms)

        # The alarm thresholds
        self.COPY_PIP_min = self.__PIP_min
        self.COPY_PIP_max = self.__PIP_max
        self.COPY_PIP_lastset = self.__PIP_lastset
        self.COPY_PIP_time_min = self.__PIP_time_min 
        self.COPY_PIP_time_max = self.__PIP_time_max
        self.COPY_PIP_time_lastset = self.__PIP_time_lastset
        self.COPY_PEEP_min = self.__PEEP_min
        self.COPY_PEEP_max = self.__PEEP_max
        self.COPY_PEEP_lastset = self.__PEEP_lastset
        self.COPY_PEEP_time_min = self.__PEEP_time_min
        self.COPY_PEEP_time_max = self.__PEEP_time_max
        self.COPY_PEEP_time_lastset = self.__PEEP_time_lastset
        self.COPY_bpm_min = self.__bpm_min 
        self.COPY_bpm_max = self.__bpm_max
        self.COPY_bpm_lastset = self.__bpm_lastset
        self.COPY_I_phase_min = self.__I_phase_min
        self.COPY_I_phase_max = self.__I_phase_max
        self.COPY_I_phase_lastset = self.__I_phase_lastset

        self._lock.release()

    def _sensor_to_COPY(self):
        # These variables have to come from the hardware
        self._lock.acquire()
        # Make sure you have acquire and release!
        self._lock.release()
        pass

    def _controls_from_COPY(self):
        # Update SET variables
        self._lock.acquire()

        #Update values
        self.__SET_PIP       = self.COPY_SET_PIP
        self.__SET_PIP_TIME  = self.COPY_SET_PIP_TIME
        self.__SET_PEEP      = self.COPY_SET_PEEP
        self.__SET_PEEP_TIME = self.COPY_SET_PEEP_TIME
        self.__SET_BPM       = self.COPY_SET_BPM
        self.__SET_I_PHASE   = self.COPY_SET_I_PHASE

        #Update derived values
        self.__SET_CYCLE_DURATION = 60 / self.__SET_BPM
        self.__SET_E_PHASE = self.__SET_CYCLE_DURATION - self.__SET_I_PHASE
        self.__SET_T_PLATEAU = self.__SET_I_PHASE - self.__SET_PIP_TIME
        self.__SET_T_PEEP = self.__SET_E_PHASE - self.__SET_PEEP_TIME

        #Update new confidence intervals
        self.__PIP_min          = self.COPY_PIP_min
        self.__PIP_max          = self.COPY_PIP_max 
        self.__PIP_lastset      = self.COPY_PIP_lastset  
        self.__PIP_time_min     = self.COPY_PIP_time_min  
        self.__PIP_time_max     = self.COPY_PIP_time_max  
        self.__PIP_time_lastset = self.COPY_PIP_time_lastset  
        self.__PEEP_min         = self.COPY_PEEP_min 
        self.__PEEP_max         = self.COPY_PEEP_max  
        self.__PEEP_lastset     = self.COPY_PEEP_lastset
        self.__PEEP_time_min    = self.COPY_PEEP_time_min
        self.__PEEP_time_max    = self.COPY_PEEP_time_max
        self.__PEEP_time_lastset = self.COPY_PEEP_time_lastset
        self.__bpm_min          = self.COPY_bpm_min 
        self.__bpm_max          = self.COPY_bpm_max  
        self.__bpm_lastset      = self.COPY_bpm_lastset  
        self.__I_phase_min      = self.COPY_I_phase_min  
        self.__I_phase_max      = self.COPY_I_phase_max 
        self.__I_phase_lastset  = self.COPY_I_phase_lastset  

        self._lock.release()

    def __test_critical_levels(self, min, max, value, name):
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
        pass
        # if (value < min) or (value > max):  # If the variable is not within limits
        #     if name not in self.__active_alarms.keys():  # And and alarm for that variable doesn't exist yet -> RAISE ALARM.
        #         new_alarm = Alarm(alarm_name=name, active=True, severity=AlarmSeverity.HIGH, value=value,
        #                           start_time=time.time(), alarm_end_time=None)
        #         self.__active_alarms[name] = new_alarm
        # else:  # Else: if the variable is within bounds,
        #     if name in self.__active_alarms.keys():  # And an alarm exists -> inactivate it.
        #         old_alarm = self.__active_alarms[name]
        #         old_alarm.alarm_end_time = time.time()
        #         old_alarm.active = False
        #         self.__logged_alarms.append(old_alarm)
        #         del self.__active_alarms[name]

    def __analyze_last_waveform(self):
        ''' This goes through the last waveform, and updates VTE, PEEP, PIP, PIP_TIME, I_PHASE, FIRST_PEEP and BPM.'''
        if len(self.__cycle_waveform_archive) > 1:  # Only if there was a previous cycle
            data = self.__cycle_waveform_archive[-1]
            phase = data[:, 0]
            pressure = data[:, 1]
            mean_pressure = np.mean(pressure)
            volume = data[:, 2]

            self._DATA_VTE = np.max(volume) - np.min(volume)

            # get the pressure niveau heuristically (much faster than fitting)
            # 20/80 percentile of pressure values below/above mean
            # Assumption: waveform is mostly between both plateaus
            if np.isfinite(mean_pressure):
                self._DATA_PEEP = np.percentile(pressure[ pressure < mean_pressure], 20 )
                self._DATA_PIP_PLATEAU  = np.percentile(pressure[ pressure > mean_pressure], 80 )
                self._DATA_PIP  = np.percentile(pressure[ pressure > mean_pressure], 95 )             #PIP is defined as the maximum, here 95% to account for outliers
                self._DATA_PIP_TIME = phase[np.min(np.where(pressure > self._DATA_PIP_PLATEAU*0.9))]
                self._DATA_I_PHASE = phase[np.max(np.where(pressure > self._DATA_PIP_PLATEAU*0.9))]
            else:
                self._DATA_PEEP = np.nan
                self._DATA_PIP_PLATEAU  = np.nan
                self._DATA_PIP  = np.nan
                self._DATA_PIP_TIME = np.nan
                self._DATA_I_PHASE = np.nan

            # and measure the breaths per minute
            self._DATA_BPM = 60. / phase[-1]  # 60 sec divided by the duration of last waveform

    def __update_alarms(self):
        ''' This goes through the values obtained from the last waveform, and updates alarms.'''
        if len(self.__cycle_waveform_archive) > 1 : # Only if there was a previous cycle
            self.__test_critical_levels(min=self.__PIP_min, max=self.__PIP_max, value=self._DATA_PIP, name=ValueName.PIP)
            self.__test_critical_levels(min=self.__PIP_time_min, max=self.__PIP_time_max, value=self._DATA_PIP_TIME, name=ValueName.PIP_TIME)
            self.__test_critical_levels(min=self.__PEEP_min, max=self.__PEEP_max, value=self._DATA_PEEP, name=ValueName.PEEP)
            self.__test_critical_levels(min=self.__bpm_min, max=self.__bpm_max, value=self._DATA_BPM, name=ValueName.BREATHS_PER_MINUTE)
            self.__test_critical_levels(min=self.__I_phase_min, max=self.__I_phase_max, value=self._DATA_I_PHASE, name=ValueName.INSPIRATION_TIME_SEC)

    def get_sensors(self) -> SensorValues:
        # Make sure to return a copy of the instance
        self._lock.acquire()
        #cp = copy.deepcopy( self.COPY_sensor_values )
        # don't need to deepcopy because a new SensorValues object is created
        # each time and it copies each individual value as it's created
        cp = copy.copy(self.COPY_sensor_values)
        self._lock.release()
        return cp

    # def get_alarms(self) -> List[Alarm]:
    #     # Returns all alarms as a list
    #     self._lock.acquire()
    #     new_alarm_list = self.COPY_logged_alarms.copy()
    #     for alarm_key in self.COPY_active_alarms.keys():
    #         new_alarm_list.append(self.COPY_active_alarms[alarm_key])
    #     self._lock.release()
    #     return new_alarm_list

    def get_active_alarms(self):
        # Returns only the active alarms
        self._lock.acquire()
        active_alarms = self.COPY_active_alarms.copy() # Make sure to return a copy
        self._lock.release()
        return active_alarms

    def get_logged_alarms(self) -> List[Alarm]:
        # Returns only the inactive alarms
        self._lock.acquire()
        logged_alarms = self.COPY_logged_alarms.copy()
        self._lock.release()
        return logged_alarms



    def set_control(self, control_setting: ControlSetting):
        ''' Updates the entry of COPY contained in the control settings'''
        self._lock.acquire()

        if control_setting.name == ValueName.PIP:
            self.COPY_SET_PIP = control_setting.value
            self.COPY_PIP_min = control_setting.min_value
            self.COPY_PIP_max = control_setting.max_value
            self.COPY_PIP_lastset = control_setting.timestamp

        elif control_setting.name == ValueName.PIP_TIME:
            self.COPY_SET_PIP_TIME = control_setting.value
            self.COPY_PIP_time_min = control_setting.min_value
            self.COPY_PIP_time_max = control_setting.max_value
            self.COPY_PIP_time_lastset = control_setting.timestamp

        elif control_setting.name == ValueName.PEEP:
            self.COPY_SET_PEEP = control_setting.value
            self.COPY_PEEP_min = control_setting.min_value
            self.COPY_PEEP_max = control_setting.max_value
            self.COPY_PEEP_lastset = control_setting.timestamp

        elif control_setting.name == ValueName.BREATHS_PER_MINUTE:
            self.COPY_SET_BPM = control_setting.value
            self.COPY_bpm_min = control_setting.min_value
            self.COPY_bpm_max = control_setting.max_value
            self.COPY_bpm_lastset = control_setting.timestamp

        elif control_setting.name == ValueName.INSPIRATION_TIME_SEC:
            self.COPY_SET_I_PHASE = control_setting.value
            self.COPY_I_phase_min = control_setting.min_value
            self.COPY_I_phase_max = control_setting.max_value
            self.COPY_I_phase_lastset = control_setting.timestamp

        elif control_setting.name == ValueName.PEEP_TIME:
            self.COPY_SET_PEEP_TIME = control_setting.value
            self.COPY_PEEP_min = control_setting.min_value
            self.COPY_PEEP_max = control_setting.max_value
            self.COPY_PEEP_lastset = control_setting.timestamp

        else:
            raise KeyError("You cannot set the variabe: " + str(control_setting.name))

        self._lock.release()

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        ''' Gets values of the COPY of the control settings. '''
        
        self._lock.acquire()
        if control_setting_name == ValueName.PIP:
            return_value = ControlSetting(control_setting_name,
                                  self.COPY_SET_PIP,
                                  self.COPY_PIP_min,
                                  self.COPY_PIP_max,
                                  self.COPY_PIP_lastset)
        elif control_setting_name == ValueName.PIP_TIME:
            return_value = ControlSetting(control_setting_name,
                                  self.COPY_SET_PIP_TIME,
                                  self.COPY_PIP_time_min,
                                  self.COPY_PIP_time_max,
                                  self.COPY_PIP_time_lastset, )
        elif control_setting_name == ValueName.PEEP:
            return_value = ControlSetting(control_setting_name,
                                  self.COPY_SET_PEEP,
                                  self.COPY_PEEP_min,
                                  self.COPY_PEEP_max,
                                  self.COPY_PEEP_lastset)
        elif control_setting_name == ValueName.BREATHS_PER_MINUTE:
            return_value = ControlSetting(control_setting_name,
                                  self.COPY_SET_BPM,
                                  self.COPY_bpm_min,
                                  self.COPY_bpm_max,
                                  self.COPY_bpm_lastset)
        elif control_setting_name == ValueName.INSPIRATION_TIME_SEC:
            return_value = ControlSetting(control_setting_name,
                                  self.COPY_SET_I_PHASE,
                                  self.COPY_I_phase_min,
                                  self.COPY_I_phase_max,
                                  self.COPY_I_phase_lastset)
        elif control_setting_name == ValueName.PEEP_TIME:
            return_value = ControlSetting(control_setting_name,
                                          self.COPY_SET_PEEP_TIME,
                                          self.COPY_PEEP_time_min,
                                          self.COPY_PEEP_time_max,
                                          self.COPY_PEEP_time_lastset)
        else:
            raise KeyError("You cannot set the variabe: " + str(control_setting_name))

        self._lock.release()

        return return_value


    def __get_PID_error(self, ytarget, yis, dt):
        error_new = ytarget - yis                   # New value of the error

        RC = 0.5  # Time constant in seconds
        s = dt / (dt + RC)
        self._DATA_I = self._DATA_I + s*(error_new - self._DATA_I)     # Integral term on some timescale RC
        self._DATA_D = error_new - self._DATA_P
        self._DATA_P = error_new

    def __calculate_control_signal_in(self):
        self.__control_signal_in  = 0            # Some setting for the maximum flow.
        self.__control_signal_in +=  self.__KP*self._DATA_P
        self.__control_signal_in +=  self.__KI*self._DATA_I
        self.__control_signal_in +=  self.__KD*self._DATA_D

    def _get_control_signal_in(self):
        ''' This is the PID controlled signal on the inspiratory side '''
        return self.__control_signal_in

    def _get_control_signal_out(self):
        ''' This is the control signal (open/close) on the expiratory side '''
        return self.__control_signal_out

    def _PID_reset(self):
        ''' resets the PID cycle to zero'''
        self.__cycle_start = time.time()

    def _PID_update(self, dt):
        ''' 
        This instantiates the control algorithms.
        During the breathing cycle, it goes through the four states:
           1) Rise to PIP
           2) Sustain PIP pressure
           3) Quick fall to PEEP
           4) Sustaint PEEP pressure
        Once the cycle is complete, it checks the cycle for any alarms, and starts a new one.
        A record of pressure/volume waveforms is kept in self.__cycle_waveform_archive

            dt: Time since last update in seconds 

        '''
        now = time.time()
        cycle_phase = now - self.__cycle_start
        next_cycle = False

        self.__DATA_VOLUME += dt * ( self._DATA_Qin - self._DATA_Qout )  # Integrate what has happened within the last few seconds from the measurements of Qin and Qout

        if cycle_phase < self.__SET_PIP_TIME:

            if self._pid_control_flag:
                target_pressure = cycle_phase*(self.__SET_PIP - self.__SET_PEEP) / self.__SET_PIP_TIME  + self.__SET_PEEP
                self.__get_PID_error(yis = self._DATA_PRESSURE, ytarget = target_pressure, dt = dt)
                self.__calculate_control_signal_in()
                self.__control_signal_out = 0   # close out valve
                if self._DATA_PRESSURE > self.__SET_PIP:
                    self.__control_signal_in = 0
            else:
                self.__control_signal_in = np.inf                                                        # STATE CONTROL: to PIP, air in as fast as possible
                self.__control_signal_out = 0
                if self._DATA_PRESSURE > self.__SET_PIP:
                    self.__control_signal_in = 0

        elif cycle_phase < self.__SET_I_PHASE:                                                           # then, we control PIP
            if self._pid_control_flag:
                self.__get_PID_error(yis = self._DATA_PRESSURE, ytarget = self.__SET_PIP, dt = dt)
                self.__calculate_control_signal_in()
                if self._DATA_PRESSURE > self.__SET_PIP+0.5:                                              
                    self.__control_signal_out = 1                                                        # if exceeded, we open the exhaust valve
                else:
                    self.__control_signal_out = 0                                                        # close out valve
            else:
                self.__control_signal_in = 0                                                             # STATE CONTROL: keep PIP plateau, let air in if below
                self.__control_signal_out = 0
                if self._DATA_PRESSURE < self.__SET_PIP:
                    self.__control_signal_in = np.inf
                if self._DATA_PRESSURE > self.__SET_PIP:
                    self.__control_signal_out = 1

        elif cycle_phase < self.__SET_PEEP_TIME + self.__SET_I_PHASE:                                     # then, we drop pressure to PEEP
            if self._pid_control_flag:
                target_pressure = self.__SET_PIP - (cycle_phase - self.__SET_I_PHASE) * (self.__SET_PIP - self.__SET_PEEP) / self.__SET_PEEP_TIME
                self.__get_PID_error(yis = self._DATA_PRESSURE, ytarget = target_pressure, dt = dt)
                self.__calculate_control_signal_in()
                self.__control_signal_out =  1
                if self._DATA_PRESSURE < self.__SET_PEEP - 1:
                    self.__control_signal_out = 0
                    self.__control_signal_in = 0
            else:
                self.__control_signal_in = 0
                self.__control_signal_out = 1
                if self._DATA_PRESSURE < self.__SET_PEEP:
                    self.__control_signal_out = 0
        elif cycle_phase < self.__SET_CYCLE_DURATION:                                                     # and control around PEEP
            if self._pid_control_flag:
                self.__get_PID_error(yis = self._DATA_PRESSURE, ytarget = self.__SET_PEEP, dt = dt)
                self.__calculate_control_signal_in()
                if self._DATA_PRESSURE > self.__SET_PEEP + 1:
                    self.__control_signal_out = 1
                else:
                    self.__control_signal_out = 0
            else:                                                                                         # STATE CONTROL: keeping PEEP, let air in if below
                self.__control_signal_in = 0
                self.__control_signal_out = 0
                if self._DATA_PRESSURE < self.__SET_PEEP:
                    self.__control_signal_in = np.inf
                if self._DATA_PRESSURE > self.__SET_PEEP:
                    self.__control_signal_out = 1

        else:
            self.__cycle_start = time.time()  # New cycle starts
            self.__DATA_VOLUME = 0            # ... start at zero volume in the lung
            self._DATA_dpdt    = 0            # and restart the rolling average for the dP/dt estimation
            next_cycle = True
        
        if next_cycle:                        # if a new breath cycle has started
            # increment breath_cycle tracker
            self._DATA_BREATH_COUNT = next(self._breath_counter)
            if len(self.__cycle_waveform) > 1:
                self.__cycle_waveform_archive.append( self.__cycle_waveform )
            self.__cycle_waveform = np.array([[0, self._DATA_PRESSURE, self.__DATA_VOLUME]])
            self.__analyze_last_waveform()    # Analyze last waveform
            self.__update_alarms()            # Run alarm detection over last cycle's waveform
            self._sensor_to_COPY()            # Get the fit values from the last waveform directly into sensor values
        else:
            self.__cycle_waveform = np.append(self.__cycle_waveform, [[cycle_phase, self._DATA_PRESSURE, self.__DATA_VOLUME]], axis=0)

    def get_past_waveforms(self):
        # Returns a list of past waveforms.
        # Format:
        #     Returns a list of [Nx3] waveforms, of [time, pressure, volume]
        #     Most recent entry is waveform_list[-1]
        # Note:
        #     After calling this function, archive is emptied!
        self._lock.acquire()
        archive = list( self.__cycle_waveform_archive ) # Make sure to return a copy as a list
        self.__cycle_waveform_archive = deque(maxlen = self._RINGBUFFER_SIZE)
        self.__cycle_waveform_archive.append(archive[-1])
        self._lock.release()
        return archive

    def get_target_waveform(self):
        # Returns the target waveform, drawn as a sketch of a stepwise linear function
        # Format is time-points, pressure values - to be connected with straight lines
        #         ______
        #        /      \                         <- Sketch waveform of single breath cycle
        #       /        \
        #      /          \____________
        #
        #     ^  ^     ^  ^           ^
        #     A  B     C  D           E           <- Critical time points

        self._lock.acquire()
        wv = (
        (0, self.__SET_PEEP),                                            # A: start of the waveform
        (self.__SET_PIP_TIME, self.__SET_PIP),                           # B: reaching PIP within PIP_TIME
        (self.__SET_I_PHASE, self.__SET_PIP),                            # C: keeping the plateau during I_Phase
        (self.__SET_PEEP_TIME + self.__SET_I_PHASE, self.__SET_PEEP),    # D: reaching PEEP within PEEP TIME
        (self.__SET_CYCLE_DURATION, self.__SET_PEEP))                    # E: Cycle ends
        self._lock.release()
        return wv

    def _start_mainloop(self):
        # This will depend on simulation or reality
        pass   

    def start(self):
        if self.__thread is None or not self.__thread.is_alive():  # If the previous thread has been stopped, make a new one.
            self._running.set()
            self.__thread = threading.Thread(target=self._start_mainloop, daemon=True)
            self.__thread.start()
        else:
            print("Main Loop already running.")

    def stop(self):
        if self.__thread is not None and self.__thread.is_alive():
            self._running.clear()
        else:
            print("Main Loop is not running.")

    def is_running(self):
        # TODO: this should be better thread-safe variable
        return self._running.is_set()

    def do_pid_control(self):
        if self._pid_control_flag:
            print("Already running PID control.")
        self._pid_control_flag = True

    def do_state_control(self):
        if not self._pid_control_flag:
            print("Already running State control.")
        self._pid_control_flag = False


class ControlModuleDevice(ControlModuleBase):
    # Implement ControlModuleBase functions
    def __init__(self):
        ControlModuleBase.__init__(self)
        self.HAL = io.Hal()
        self._sensor_to_COPY()
        
    def _sensor_to_COPY(self):
        # And the sensor measurements
        self._lock.acquire()
        self.COPY_sensor_values = SensorValues(vals={
            ValueName.PIP.name                  : self._DATA_PIP,
            ValueName.PEEP.name                 : self._DATA_PEEP,
            ValueName.FIO2.name                 : 70,
            ValueName.TEMP.name                 : -1,
            ValueName.HUMIDITY.name             : -1,
            ValueName.PRESSURE.name             : self.HAL.pressure,
            ValueName.VTE.name                  : self._DATA_VTE,
            ValueName.BREATHS_PER_MINUTE.name   : self._DATA_BPM,
            ValueName.INSPIRATION_TIME_SEC.name : self._DATA_I_PHASE,
            'timestamp'                  : time.time(),
            'loop_counter'             : self._loop_counter,
            'breath_count': self._DATA_BREATH_COUNT
        })
        self._lock.release()

    def _start_mainloop(self):
        # start running, this should be run as a thread! 
        # Compare to initialization in Base Class!

        update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE

        while self._running:
            time.sleep(self._LOOP_UPDATE_TIME)
            self._loop_counter += 1
            now = time.time()
            dt = now - self._last_update                            # Time sincle last cycle of main-loop

            if dt > CONTROL[ValueName.BREATHS_PER_MINUTE].default / 4:                                                      # TODO: RAISE HARDWARE ALARM, no update should be so long
                print("Restarted cycle.")
                self._PID_reset()
                dt = self._LOOP_UPDATE_TIME

            self._DATA_PRESSURE = self.HAL.pressure                 # Get a pressure measurement from HAL

            self._PID_update(dt = dt)                               # Update the PID Controller

            valve_open_in = self._get_control_signal_in()           # Inspiratory side: get control signal for PropValve
            self.HAL.setpoint_in = max(min(100, valve_open_in), 0)

            self.HAL.setpoint_ex = self._get_control_signal_out()          # Expiratory side: get control signal for Solenoid
            '''
            if(self.HAL.setpoint_ex == 0):
                self.HAL._expiratory_valve.close()
            else:
                self.HAL._expiratory_valve.open()
            '''

            self._DATA_Qout = self.HAL.flow_ex                     # Flow sensor on Expiratory side
            self._DATA_Qin  = self.HAL.flow_in                      # Flow sensor on inspiratory side. NOTE: used to calculate VTE
            self._last_update = now

            if update_copies == 0:
                self._controls_from_COPY()     # Update controls from possibly updated values as a chunk
                self._alarm_to_COPY()          # Copy current alarms and settings to COPY
                self._sensor_to_COPY()         # Copy sensor values to COPY
                update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
            else:
                update_copies -= 1

        # # get final values on stop
        self._controls_from_COPY()  # Update controls from possibly updated values as a chunk
        self._alarm_to_COPY()  # Copy current alarms and settings to COPY
        self._sensor_to_COPY()  # Copy sensor values to COPY



class Balloon_Simulator:
    '''
    This is a imple physics simulator for inflating a balloon. 
    For math, see https://en.wikipedia.org/wiki/Two-balloon_experiment
    '''

    def __init__(self, leak):
        # Hard parameters for the simulation
        self.max_volume = 6    # Liters  - 6?
        self.min_volume = 1.5  # Liters - baloon starts slightly inflated.
        self.PC = 40           # Proportionality constant that relates pressure to cm-H2O
        self.P0 = 0            # Baseline/Minimum pressure.
        self.leak = leak

        self.temperature = 37  # keep track of these, as they are important output variable
        self.humidity = 90
        self.fio2 = 60

        # Dynamical parameters - these are the initial conditions
        self.current_flow     = 0  # in unit  liters/sec

        self.set_Qin          = 0  # set flow of a prop valve on inspiratory side      -- liters/second
        self.Qin              = 0  # exact flow of a prop valve on inspiratory side    -- liters/second

        self.set_Qout         = 0  # 0|max - setting of an solenoid on expiratory side -- liters/second
        self.Qout             = 0  # exact flow through the solenoid

        self.current_pressure = 0  # in unit  cm-H2O
        self.r_real = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)  # size of the lung
        self.current_volume = self.min_volume                         # in unit  liters

    def get_pressure(self):
        return self.current_pressure

    def get_volume(self):
        return self.current_volume

    def set_flow_in(self, Qin, dt):
        self.set_Qin = Qin

        Qin_clip = np.min([Qin, 2])                # Flows have to be positive, and reasonable. Nothing here is faster that 2 l/s
        Qin_clip = np.max([Qin_clip, 0])
        self.Qin     = Qin_clip                    # Assume the set-value is also the true value for prop

    def set_flow_out(self, Qout, dt):
        self.set_Qout = Qout

        Qout_clip = np.min([Qout, 2])                    # Flows have to be positive, and reasonable. Nothing here is faster that 2 l/s
        Qout_clip = np.max([Qout_clip, 0])
        difference_pressure = self.current_pressure - 0  # Convention: outside is "0"
        conductance = 0.05*Qout_clip                     # This should be in the range of ~1 liter/s for typical max pressure differences
        self.Qout = difference_pressure * conductance    # Target for flow out

    def update(self, dt):  # Performs an update of duration dt [seconds]

        if dt<1:                                        # This is the simulation, so not quite so important,
            self.current_flow = self.Qin - self.Qout     # But no update should take longer than that
            self.current_volume += self.current_flow * dt

            if self.leak:
                RC = 5  # pulled 5 sec out of my hat
                s = dt / (RC + dt)
                self.current_volume = self.current_volume + s * (self.min_volume - self.current_volume)

            # This is from the baloon equation, uses helper variable (the baloon radius)
            self.r_real = (3 * self.current_volume / (4 * np.pi)) ** (1 / 3)
            r0 = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)

            self.current_pressure = self.P0 + (self.PC / (r0 ** 2 * self.r_real)) * (1 - (r0 / self.r_real) ** 6)

            # Temperature, humidity and o2 fluctuations modelled as OUprocess
            self.temperature = self.OUupdate(self.temperature, dt=dt, mu=37, sigma=0.3, tau=1)
            self.fio2 = self.OUupdate(self.fio2, dt=dt, mu=60, sigma=5, tau=1)
            self.humidity = self.OUupdate(self.humidity, dt=dt, mu=90, sigma=5, tau=1)
            if self.humidity > 100:
                self.humidity = 100
        else:
            self._reset()
            print(self.current_pressure)


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
        dt = max(dt, 0.05)  #Make sure this doesn't go haywire if anything hangs. Max 50ms
        sigma_bis = sigma * np.sqrt(2. / tau)
        sqrtdt = np.sqrt(dt)
        new_variable = variable + dt * (-(variable - mu) / tau) + sigma_bis * sqrtdt * np.random.randn()
        return new_variable

    def _reset(self):
        ''' resets the ballon to standard parameters. '''
        self.set_Qin          = 0
        self.Qin              = 0
        self.set_Qout         = 0
        self.Qout             = 0
        self.current_pressure = 0
        self.r_real = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)
        self.current_volume = self.min_volume

class ControlModuleSimulator(ControlModuleBase):
    # Implement ControlModuleBase functions
    def __init__(self):
        ControlModuleBase.__init__(self)
        self.Balloon = Balloon_Simulator(leak=False)          # This is the simulation
        self._sensor_to_COPY()

    def __SimulatedPropValve(self, x, dt):
        '''
        This simulates the action of a proportional valve.
        Flow-current-curve eye-balled from the datasheet of SMC PVQ31-5G-23-01N  
        https://www.ocpneumatics.com/content/pdfs/PVQ.pdf
        
        x:  Input current [mA]
        dt: Time since last setting in seconds [for the LP filter]
        '''
        flow_new = 1.0*(np.tanh(0.03*(x - 130)) + 1)
        if x>160:
            flow_new = 1.72  #Maximum, ~100 l/min
        if x<0:
            flow_new = 0
        return flow_new

    def __SimulatedSolenoid(self, x):
        '''
        Depending on x, set flow to a binary value.
        Here: flow is either 0 or 1l/sec
        '''
        if x > 0:
            return 1
        else:
            return 0

    def _sensor_to_COPY(self):
        # And the sensor measurements
        self._lock.acquire()
        self.COPY_sensor_values = SensorValues(vals={
            ValueName.PIP.name                  : self._DATA_PIP,
            ValueName.PEEP.name                 : self._DATA_PEEP,
            ValueName.FIO2.name                 : self.Balloon.fio2,
            ValueName.TEMP.name                 : self.Balloon.temperature,
            ValueName.HUMIDITY.name             : self.Balloon.humidity,
            ValueName.PRESSURE.name             : self.Balloon.current_pressure,
            ValueName.VTE.name                  : self._DATA_VTE,
            ValueName.BREATHS_PER_MINUTE.name   : self._DATA_BPM,
            ValueName.INSPIRATION_TIME_SEC.name : self._DATA_I_PHASE,
            'timestamp'                  : time.time(),
            'loop_counter'             : self._loop_counter,
            'breath_count': self._DATA_BREATH_COUNT
        })
        self._lock.release()

    def _start_mainloop(self):
        # start running, this should be run as a thread! 
        # Compare to initialization in Base Class!

        update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE

        while self._running.is_set():
            time.sleep(self._LOOP_UPDATE_TIME)
            self._loop_counter += 1
            now = time.time()
            dt = now - self._last_update                            # Time sincle last cycle of main-loop
            if dt > CONTROL[ValueName.BREATHS_PER_MINUTE].default / 4:                                                         # TODO: RAISE HARDWARE ALARM, no update should take that long
                print("Restarted cycle.")
                self._PID_reset()
                self.Balloon._reset()
                dt = self._LOOP_UPDATE_TIME

            self.Balloon.update(dt = dt)                            # Update the state of the balloon simulation
            self._DATA_PRESSURE = self.Balloon.get_pressure()       # Get a pressure measurement from balloon and tell controller             --- SENSOR 1

            self._PID_update(dt = dt)                               # Update the PID Controller

            x = self._get_control_signal_in()                       # Inspiratory side: get control signal for PropValve
            Qin = self.__SimulatedPropValve(x, dt = dt)             # And calculate the produced flow Qin

            y = self._get_control_signal_out()                      # Expiratory side: get control signal for Solenoid
            Qout = self.__SimulatedSolenoid(y)                      # Set expiratory flow rate, Qout

            self.Balloon.set_flow_in(Qin, dt = dt)                  # Set the flow rates for the Balloon simulator
            self.Balloon.set_flow_out(Qout, dt = dt)

            self._DATA_Qout = self.Balloon.Qout                     # Tell controller the expiratory flow rate, _DATA_Qout                    --- SENSOR 2
            self._DATA_Qin  = self.Balloon.Qin                      # Tell controller the expiratory flow rate, _DATA_Qin                     --- SENSOR 3
            self._last_update = now

            if update_copies == 0:
                self._controls_from_COPY()     # Update controls from possibly updated values as a chunk
                self._alarm_to_COPY()          # Copy current alarms and settings to COPY
                self._sensor_to_COPY()         # Copy sensor values to COPY
                update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
            else:
                update_copies -= 1

        # # get final values on stop
        self._controls_from_COPY()  # Update controls from possibly updated values as a chunk
        self._alarm_to_COPY()  # Copy current alarms and settings to COPY
        self._sensor_to_COPY()  # Copy sensor values to COPY




def get_control_module(sim_mode=False):
    if sim_mode == True:
        return ControlModuleSimulator()
    else:
        return ControlModuleDevice()