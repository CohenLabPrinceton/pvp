import time
import typing
from typing import List
import threading
import numpy as np
import copy
from collections import deque
import pdb
from itertools import count
import signal
import pytest

import pvp.io as io

from pvp.common.message import SensorValues, ControlValues, ControlSetting, DerivedValues
from pvp.common.loggers import init_logger, DataLogger
from pvp.common.values import CONTROL, ValueName
from pvp.common.utils import timeout
from pvp.alarm import ALARM_RULES, AlarmType, AlarmSeverity, Alarm
from pvp import prefs


class ControlModuleBase:
    """

    Abstract controller class for simulation/hardware.

    1. General notes:
    All internal variables fall in three classes, denoted by the beginning of the variable:
        - `COPY_varname`: These are copies (for safe threading purposes) that are regularly sync'ed with internal variables.
        - `__varname`:    These are variables only used in the ControlModuleBase-Class
        - `_varname`:     These are variables used in derived classes.

    2. Set and get values.
    Internal variables should only to be accessed though the set_ and get_ functions.
        These functions act on COPIES of internal variables (`__` and `_`), that are sync'd every few
        iterations. How often this is done is adjusted by the variable
        `self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE`. To avoid multiple threads manipulating the same
        variables at the same time, every manipulation of `COPY_` is surrounded by a thread lock.

    Public Methods:
        - `get_sensors()`:                     Returns a copy of the current sensor values.
        - `get_alarms()`:                      Returns a List of all alarms, active and logged
        - `get_control(ControlSetting)`:       Sets a controll-setting. Is updated at latest within self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
        - `get_past_waveforms()`:              Returns a List of waveforms of pressure and volume during at the last N breath cycles, N<self. _RINGBUFFER_SIZE, AND clears this archive.
        - `start()`:                           Starts the main-loop of the controller
        - `stop()`:                            Stops the main-loop of the controller
        - `set_control()`:                     Set the control
        - `is_running()`:                      Returns a bool whether the main-thread is running
        - `get_heartbeat()`:                   Returns a heartbeat, more specifically, the continuously increasing iteration-number of the main control loop.
    """

    def __init__(self, save_logs: bool = False, flush_every: int = 10):
        """
        Initializes the ControlModuleBase class.

        Args:
            save_logs (bool, optional): Should sensor data and controls should be saved with the :class:`.DataLogger`? Defaults to False.
            flush_every (int, optional): Flush and rotate logs every n breath cycles. Defaults to 10.

        Raises:
            alert: [description]
        """

        self.logger = init_logger(__name__)
        self.logger.info('controller init')

        #####################  Algorithm/Program parameters  ##################
        # Hyper-Parameters
        # TODO: These should probably all (or whichever make sense) should be args to __init__ -jls
        self._LOOP_UPDATE_TIME                   = prefs.get_pref('CONTROLLER_LOOP_UPDATE_TIME')    # Run the main control loop every 0.01 sec
        self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE = prefs.get_pref('CONTROLLER_LOOPS_UNTIL_UPDATE')  # After every 10 main control loop iterations, update COPYs.
        self._RINGBUFFER_SIZE                    = prefs.get_pref('CONTROLLER_RINGBUFFER_SIZE')     # Maximum number of breath cycles kept in memory
        self._save_logs                          = save_logs   # Keep logs in a file
        self._FLUSH_EVERY                        = flush_every

        #########################  Control management  #########################

        # This is what the machine has controll over:
        self.__control_signal_in  = 0              # State of a valve on the inspiratory side - could be a proportional valve.
        self.__control_signal_out = 0              # State of a valve on the exspiratory side - this is open/close i.e. value in (0,1)
        self.__control_signal_helpers = np.array([0., 0., 0.]) # Helper variables for multiple low-pass filters

        # Internal Control variables. "SET" indicates that this is set.
        self.__SET_PIP       = CONTROL[ValueName.PIP].default                     # Target PIP pressure
        self.__SET_PIP_GAIN  = CONTROL[ValueName.PIP_TIME].default                # Target time to reach PIP in seconds
        self.__SET_PEEP      = CONTROL[ValueName.PEEP].default                    # Target PEEP pressure
        self.__SET_PEEP_TIME = CONTROL[ValueName.PEEP_TIME].default               # Target time to reach PEEP from PIP plateau
        self.__SET_BPM       = CONTROL[ValueName.BREATHS_PER_MINUTE].default      # Target breaths per minute
        self.__SET_I_PHASE   = CONTROL[ValueName.INSPIRATION_TIME_SEC].default    # Target duration of inspiratory phase

        # Derived internal control variables - fully defined by numbers above
        self.__SET_CYCLE_DURATION = 60 / self.__SET_BPM

        self.__SET_E_PHASE        = self.__SET_CYCLE_DURATION - self.__SET_I_PHASE
        self.__SET_T_PEEP         = self.__SET_E_PHASE - self.__SET_PEEP_TIME

        #########################  Alarm management  #########################

        # Alarm management; controller can only react to High airway pressure alarm, and report Hardware problems
        self.HAPA = None
        self.hapa_crossing_time = None # time that the pressure first crosses the threshold
        self.TECHA = [] # type: typing.List[Alarm]
        self.limit_hapa = ALARM_RULES[AlarmType.HIGH_PRESSURE].conditions[0][1].limit # TODO: Jonny write method to get limits from alarm manager
        self.cough_duration = prefs.get_pref('COUGH_DURATION') # type: typing.Union[float, int]
        #self.breath_pressure_drop = 4 #prefs.get_pref('XXXXX')   #pressure drop below peep that is detected as an attempt to breath.
        self.breath_pressure_drop = prefs.get_pref('BREATH_PRESSURE_DROP') # type: typing.Union[float, int]
        self.breath_detection = prefs.get_pref('BREATH_DETECTION') # type: bool

        self.limit_max_flows = prefs.get_pref('CONTROLLER_MAX_FLOW')            # If flows above that, hardware cannot be correct.
        self.limit_max_pressure = prefs.get_pref('CONTROLLER_MAX_PRESSURE')       # If pressure above that, hardware cannot be correct.
        self.limit_max_stuck_sensor = prefs.get_pref('CONTROLLER_MAX_STUCK_SENSOR')   # 200 ms, jonny, wherever you want this number to live



        self.sensor_stuck_since = None

        #########################  Data management  #########################

        # These are measurements from the last breath cycle.
        self._DATA_PIP = None         # Measured value of PIP
        self._DATA_PIP_PLATEAU = None # Measured pressure of the plateau
        self._DATA_PIP_TIME = None    # Measured time of reaching PIP plateau
        self._DATA_PEEP = None        # Measured valued of PEEP
        self._DATA_PEEP_TIME = None   # Measured time of reaching PEEP
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
        self._cycle_start = time.time()
        self.__cycle_waveform = np.array([[0, 0, 0]])                            # To build up the current cycle's waveform
        self.__cycle_waveform_archive = deque(maxlen = self._RINGBUFFER_SIZE)          # An archive of past waveforms.

        # These are measurements that change from timepoint to timepoint
        self._DATA_PRESSURE = 0
        self._DATA_VOLUME   = 0
        self._DATA_OXYGEN   = 0
        self.COPY_DATA_OXYGEN  = 0        # Oxygen is not queried in every cycle. This is a copy of the value
        self._OXYGEN_LAST_READ = 0        # Last time the oxygen sensor was read.

        self._DATA_Qout     = 0           # Measurement of the airflow out
        self._DATA_dpdt     = 0           # Current sample of the rate of change of pressure dP/dt in cmH2O/sec
        self.__DATA_old     = None
        self._last_update   = time.time()
        self._BASELINE_ESTIMATOR_LENGTH = 500
        self._PRESSURE_AVEREAGING_LENGTH = 5
        self._flow_list = deque(maxlen = self._BASELINE_ESTIMATOR_LENGTH)          # An archive of past flows, to calculate background flow out
        self._DATA_PRESSURE_LIST = deque(maxlen = self._PRESSURE_AVEREAGING_LENGTH)

        ############### Initialize COPY variables for threads  ##############
        # COPY variables that later updated on a regular basis
        self.COPY_sensor_values = None # empty SensorValues can no longer be instantiated -jls

        ###########################  Threading init  #########################
        # Run the start() method as a thread
        self._loop_counter = 0
        self._running = threading.Event()
        self._running.clear()
        self._lock = threading.Lock()
        self._initialize_set_to_COPY()

        # self.__thread = threading.Thread(target=self._start_mainloop, daemon=True)
        # self.__thread.start()
        self.__thread = None

        ############################# Logging ################################
        # Create an instance of the DataLogger class
        self.dl = None
        if self._save_logs:
            try:
                self.dl = DataLogger()
            except OSError as e:
                # raised if not enough space
                self.logger.exception(f'couldnt start data logger, not saving logs. Got exception\n    {e}')
                self._save_logs = False

        ####################### Internal health checks ###########################
        self._time_last_contact = time.time()
        self._critical_time     = prefs.get_pref('HEARTBEAT_TIMEOUT')           #If Controller has not received set/get within the last 200 ms, it gets nervous.

    def __del__(self):
        """
        Destruction of the ControlModuleBase Class; closes the log-file.
        """
        if self._save_logs:
            self.dl.close_logfile()

    def _initialize_set_to_COPY(self):
        """
        Makes a copy of internal variables. This is used to facilitate threading
        """
        with self._lock:
        # Copy of the SET variables for threading.
            self.COPY_SET_PIP       = self.__SET_PIP 
            self.COPY_SET_PIP_TIME  = self.__SET_PIP_GAIN
            self.COPY_SET_PEEP      = self.__SET_PEEP
            self.COPY_SET_PEEP_TIME = self.__SET_PEEP_TIME
            self.COPY_SET_BPM       = self.__SET_BPM
            self.COPY_SET_I_PHASE   = self.__SET_I_PHASE

    def _sensor_to_COPY(self):        # pragma: no cover
        # These variables have to come from the hardware
        # Make sure you have acquire and release!
        pass

    def _controls_from_COPY(self):
        # Update SET variables
        with self._lock:
            #Update values
            self.__SET_PIP       = self.COPY_SET_PIP
            self.__SET_PIP_GAIN  = self.COPY_SET_PIP_TIME
            self.__SET_PEEP      = self.COPY_SET_PEEP
            self.__SET_PEEP_TIME = self.COPY_SET_PEEP_TIME
            self.__SET_BPM       = self.COPY_SET_BPM
            self.__SET_I_PHASE   = self.COPY_SET_I_PHASE

            if self.__SET_BPM > 0:
                self.__SET_CYCLE_DURATION = 60 / self.__SET_BPM

        self.__SET_E_PHASE = self.__SET_CYCLE_DURATION - self.__SET_I_PHASE
        self.__SET_T_PEEP = self.__SET_E_PHASE - self.__SET_PEEP_TIME

    def __comptest(self, phase, ls, selector):
        """Helper function to identify the index the first occurence of a number in `list` exceeding `threshold`, and returns phase[idx]

        Args:
            phase (array): a list of numbers
            list (array): array of bools with same length as phase
            selector (string): 'first' or 'last' whichever is wanted

        Returns:
            float: phase[idx] where `idx` is first, or last point where numbers in list exceed threshold
        """
        if np.sum(ls)>0: 
            if selector == 'first':
                value_at_point = phase[np.min(np.where(ls))]               # Make sure there is at least one occurance
            elif selector == 'last':
                value_at_point = phase[np.max(np.where(ls))]
        else:
            value_at_point = 0

        return value_at_point

    def __analyze_last_waveform(self):
        """
        This goes through the last waveform, and updates the internal variables:
              VTE, PEEP, PIP, PIP_TIME, I_PHASE, FIRST_PEEP and BPM.
        """
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
                if np.sum(pressure > mean_pressure) == 0:
                    self._DATA_PEEP = 0
                    self._DATA_PIP_PLATEAU = 0
                    self._DATA_PIP = 0
                else:
                    self._DATA_PEEP = np.percentile(pressure[ pressure < mean_pressure], 20 )
                    self._DATA_PIP_PLATEAU  = np.percentile(pressure[ pressure > mean_pressure], 80 )
                    self._DATA_PIP  = np.percentile(pressure[ pressure > mean_pressure], 95 )             #PIP is defined as the maximum, here 95% to account for outliers
                
                #self._DATA_PIP_TIME = phase[np.min(np.where(pressure > self._DATA_PIP_PLATEAU*0.9))]
                self._DATA_PIP_TIME = self.__comptest(phase, pressure > self._DATA_PIP_PLATEAU*0.9, 'first')

                #self._DATA_PEEP_TIME = phase[np.min(np.where(pressure < self._DATA_PEEP))]
                self._DATA_PEEP_TIME = self.__comptest(phase,pressure < self._DATA_PEEP, 'first')

                # self._DATA_I_PHASE = phase[np.max(np.where(pressure > self._DATA_PIP_PLATEAU*0.9))]
                self._DATA_I_PHASE = self.__comptest(phase, pressure > self._DATA_PIP_PLATEAU*0.9, 'last')
            else:
                self._DATA_PEEP = np.nan
                self._DATA_PIP_PLATEAU  = np.nan
                self._DATA_PIP  = np.nan
                self._DATA_PIP_TIME = np.nan
                self._DATA_PEEP_TIME = np.nan
                self._DATA_I_PHASE = np.nan

            # and measure the breaths per minute
            self._DATA_BPM = np.nan
            if phase[-1] > 0:
                self._DATA_BPM = 60. / phase[-1]  # 60 sec divided by the duration of last waveform, exception if this was 0.

            if self._save_logs:
                #And the control value instance
                derived_values = DerivedValues(
                    timestamp        = time.time(),
                    breath_count     = self._DATA_BREATH_COUNT,
                    I_phase_duration = self._DATA_I_PHASE,
                    pip_time         = self._DATA_PIP_TIME,
                    peep_time        = self._DATA_PEEP_TIME,
                    pip              = self._DATA_PIP,
                    pip_plateau      = self._DATA_PIP_PLATEAU,
                    peep             = self._DATA_PEEP, 
                    vte              = self._DATA_VTE
                )
                #And save both
                self.dl.store_derived_data(derived_values)

    def get_sensors(self) -> SensorValues:
        """
        A method callable from the outside to get a copy of sensorValues

        Returns:
            SensorValues: A set of current sensorvalues, handeled by the controller.
        """
        # Make sure to return a copy of the instance
        with self._lock:
            cp = copy.copy(self.COPY_sensor_values)
        self._time_last_contact = time.time()
        return cp

    def get_alarms(self) -> typing.Union[None, typing.Tuple[Alarm]]:
        """
        A method callable from the outside to get a copy of the alarms, that the controller checks:
        High airway pressure, and technical alarms.

        Returns:
            typing.Union[None, typing.Tuple[Alarm]]: A tuple of alarms
        """
        with self._lock:
            hapa = self.HAPA
            techa = self.TECHA

        # return a tuple of alarms if there are any.
        if (hapa is not None) and (len(techa)>0):
            ret = (hapa, techa)
        elif hapa is not None:
            ret = (hapa,)
        elif len(techa)>0:
            ret = (techa,)
        else:
            ret = None

        if ret is not None:
            self.logger.debug(f'Returning alarms {ret}')

        return ret

    def set_control(self, control_setting: ControlSetting):
        """
        A method callable from the outside to set alarms.
        This updates the entries of COPY with new control values.

        Args:
            control_setting (ControlSetting): [description]
        """
        if control_setting.value is not None:
            with self._lock:
                if control_setting.name == ValueName.PIP:
                    self.COPY_SET_PIP = control_setting.value
                elif control_setting.name == ValueName.PIP_TIME:
                    self.COPY_SET_PIP_TIME = control_setting.value
                elif control_setting.name == ValueName.PEEP:
                    self.COPY_SET_PEEP = control_setting.value
                elif control_setting.name == ValueName.BREATHS_PER_MINUTE:
                    self.COPY_SET_BPM = control_setting.value
                elif control_setting.name == ValueName.INSPIRATION_TIME_SEC:
                    self.COPY_SET_I_PHASE = control_setting.value
                elif control_setting.name == ValueName.PEEP_TIME:
                    self.COPY_SET_PEEP_TIME = control_setting.value
                else:
                    self.logger.warning(f'Could not set control {control_setting.name}, no corresponding variable in controller')
                    return

                if self._save_logs:
                    self.dl.store_control_command(control_setting)

        # PIP will pass the HAPA limit in the max_value parameter
        if control_setting.name == ValueName.PIP:
            if control_setting.max_value is not None:
                with self._lock:
                    self.limit_hapa = control_setting.max_value


        self._time_last_contact = time.time()

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        """
        A method callable from the outside to get current control settings.
        This returns values of COPY to the outside world.

        Args:
            control_setting_name (ValueName): The specific control asked for

        Returns:
            ControlSetting: ControlSettings-Object that contains relevant data
        """
        with self._lock:
            if control_setting_name == ValueName.PIP:
                return_value = ControlSetting(control_setting_name, self.COPY_SET_PIP)
            elif control_setting_name == ValueName.PIP_TIME:
                return_value = ControlSetting(control_setting_name, self.COPY_SET_PIP_TIME)
            elif control_setting_name == ValueName.PEEP:
                return_value = ControlSetting(control_setting_name, self.COPY_SET_PEEP)
            elif control_setting_name == ValueName.BREATHS_PER_MINUTE:
                return_value = ControlSetting(control_setting_name, self.COPY_SET_BPM)
            elif control_setting_name == ValueName.INSPIRATION_TIME_SEC:
                return_value = ControlSetting(control_setting_name, self.COPY_SET_I_PHASE)
            elif control_setting_name == ValueName.PEEP_TIME:
                return_value = ControlSetting(control_setting_name, self.COPY_SET_PEEP_TIME)
            else:
                self.logger.warning(
                    f'Could not get control {control_setting_name}, no corresponding variable in controller')
                return_value = None

        self._time_last_contact = time.time()
        return return_value

    def set_breath_detection(self, breath_detection: bool):
        if isinstance(breath_detection, bool):
            if self.breath_detection != breath_detection:
                self.logger.info(f'Setting breath detection mode to {breath_detection}')
                self.breath_detection = breath_detection
        else:
            self.logger.exception(f"Dont know how to set breath detection mode {breath_detection}, must be bool")

    def get_breath_detection(self) -> bool:
        """
        Return current state of autonomous breath detection

        Returns:
            bool
        """
        return self.breath_detection

    def __get_PID_error(self, ytarget, yis, dt, RC):
        """
        Calculates the three terms for PID control. Also takes a timestep "dt" on which the integral-term is smoothed.

        Args:
            ytarget (float): target value of pressure
            yis (float): current value of pressure
            dt (float): timestep
            RC (float): time constant for calculation of integral term.
        """
        error_new = ytarget - yis                                      # New value of the error

        s = dt / (dt + RC)
        self._DATA_I = self._DATA_I + s*(error_new - self._DATA_I)     # Integral term on some timescale RC  -- TODO: Improvement: add integral windup
        self._DATA_D = error_new - self._DATA_P
        self._DATA_P = error_new

    def __calculate_control_signal_in(self, dt):
        """
        Calculates the PID control signal by:
            - Combining the the three gain parameters.
            - And smoothing the control signal with a moving window of three frames (~10ms)

        Args:
            dt (float): timestep
        """

        new_value  = 0
        new_value +=  self.__KP*self._DATA_P
        new_value +=  self.__KI*self._DATA_I
        new_value +=  self.__KD*self._DATA_D

        self.__control_signal_helpers[2] = self.__control_signal_helpers[1]
        self.__control_signal_helpers[1] = self.__control_signal_helpers[0]
        self.__control_signal_helpers[0] = new_value
        self.__control_signal_in = np.mean(self.__control_signal_helpers)

    def _get_control_signal_in(self):
        """
        Produces the INSPIRATORY control-signal that has been calculated in `__calculate_control_signal_in(dt)`

        Returns:
            float: the numerical control signal for the inspiratory prop valve
        """
        return self.__control_signal_in

    def _get_control_signal_out(self):
        """
        Produces the EXPIRATORY control-signal for the different states, i.e. open/close

        Returns:
            float: numerical control signal for expiratory side: open (1) close (0)
        """
        return self.__control_signal_out

    def _control_reset(self):
        """
        Resets the internal controller cycle to zero, i.e. restarts the breath cycle.
        Used for autonomous breath detection.
        """
        self._cycle_start = time.time()

    def __test_for_alarms(self):
        """
        Implements tests that are to be executed in the main control loop:
            - Test for HAPA
            - Test for Technical Alert, making sure sensor values are plausible
            - Test for Technical Alert, make sure continuous in contact
        Currently: Alarms are time.time() of first occurance.

        """
        # for now, assume UI will send updates, we init from the default value
        # jonny will implement means of getting limits from alarm manager
        #limit_hapa =
        limit_max_flows = 10            # If flows above that, hardware cannot be correct.
        limit_max_pressure = 100        # TODO: If pressure above that, hardware cannot be correct. Should find central storge site for hardware limits
        limit_max_stuck_sensor = 0.2    # TODO: 200 ms, jonny, wherever you want this number to live

        #### First: Check for High Airway Pressure (HAPA)
        if self._DATA_PRESSURE > self.limit_hapa:
            # if just crossing, store time of threshold crossing
            if self.hapa_crossing_time is None:
                self.hapa_crossing_time = time.time()

            # check if time elapsed is greater than cough duration.
            if time.time() - self.hapa_crossing_time > self.cough_duration:       # 100 ms active to avoid being triggered by coughs
                if self.__control_signal_in != 0 and self.__control_signal_out != 1:
                    self.__control_signal_out = 1
                    self.__control_signal_in  = 0

                # create HAPA alarm
                if self.HAPA is None:
                    self.HAPA = Alarm(AlarmType.HIGH_PRESSURE,
                                      AlarmSeverity.HIGH,
                                      time.time(),
                                      value=self._DATA_PRESSURE)

                    self.logger.warning(f'Triggered HAPA at ' + str(self._DATA_PRESSURE))

        else:
            if self.hapa_crossing_time is not None and self.HAPA is None:
                self.logger.warning('Transient high pressure that did not trigger HAPA, probably a cough')
            self.HAPA = None
            self.hapa_crossing_time = None

        #### Second: Check for Technical Alerts via data plausibility:
        #  ->  Measurements change over time, and are in a plausible range
        if self.__DATA_old is None:
            self.__DATA_old = [self.COPY_DATA_OXYGEN, self._DATA_Qout, self._DATA_PRESSURE]
            inputs_dont_change = False 
        else:
            inputs_dont_change = (self.COPY_DATA_OXYGEN == self.__DATA_old[0]) and \
                                 (self._DATA_Qout == self.__DATA_old[1]) and \
                                 (self._DATA_PRESSURE == self.__DATA_old[2])
            self.__DATA_old = [self.COPY_DATA_OXYGEN, self._DATA_Qout, self._DATA_PRESSURE]

        if inputs_dont_change:
            if self.sensor_stuck_since is None:
                self.sensor_stuck_since = time.time()                # If inputs are stuck, remember the time.
                time_elapsed = 0
            else:
                time_elapsed = time.time() - self.sensor_stuck_since   # If happened again, how long?

            if time_elapsed > self.limit_max_stuck_sensor and not any([a.alarm_type == AlarmType.SENSORS_STUCK for a in self.TECHA]):
                    self.TECHA.append(Alarm(
                        AlarmType.SENSORS_STUCK,
                        AlarmSeverity.TECHNICAL,
                    ))
                    self.logger.warning(f'Inputs do not change; raised alarm.')
        else:
            self.TECHA = [a for a in self.TECHA if a.alarm_type != AlarmType.SENSORS_STUCK]
            self.sensor_stuck_since = None                           # If ok, reset sensor_stuck


        data_implausible = (self.COPY_DATA_OXYGEN < 0 or self.COPY_DATA_OXYGEN > 100) or \
                           (self._DATA_Qout < 0 or self._DATA_Qout > self.limit_max_flows) or \
                           (self._DATA_PRESSURE < 0 or self._DATA_PRESSURE > self.limit_max_pressure)
        if data_implausible:
            if not any([a.alarm_type == AlarmType.BAD_SENSOR_READINGS for a in self.TECHA]):
                self.TECHA.append(Alarm(
                    AlarmType.BAD_SENSOR_READINGS,
                    AlarmSeverity.TECHNICAL,
                ))
            self.logger.warning(f'Implausible values; raised alarm.')

        #### Third: Make sure that updates are coming in in a regular basis
        #
        last_contact = np.abs(self._time_last_contact - time.time())
        if last_contact > self._critical_time:
            if not any([a.alarm_type == AlarmType.MISSED_HEARTBEAT for a in self.TECHA]):
                self.TECHA.append(Alarm(
                    AlarmType.MISSED_HEARTBEAT,
                    AlarmSeverity.TECHNICAL,
                    message=f"Controller has not heard from coordinator in {last_contact}"
                ))

        #self.TECHA = time.time()  # Technical alert, but continue running hoping for the best

    def __start_new_breathcycle(self):
        """
        Some housekeeping. This has to be executed when the next breath cycles starts:
            - starts new breathcycle
            - initializes newe __cycle_waveform
            - analyzes last breath waveform for PIP, PEEP etc. with `__analyze_last_waveform()`
            - flushes the logfile
        """
        self._DATA_BREATH_COUNT = next(self._breath_counter)
        if len(self.__cycle_waveform) > 1:
            self.__cycle_waveform_archive.append( self.__cycle_waveform )
        self.__cycle_waveform = np.array([[0, self._DATA_PRESSURE, self._DATA_VOLUME]])
        self.__analyze_last_waveform()    # Analyze last waveform
        self._sensor_to_COPY()            # Get the fit values from the last waveform directly into sensor values

        if self._save_logs and self._DATA_BREATH_COUNT % self._FLUSH_EVERY == 0:
            self.dl.flush_logfile()        # If we kept records, flush the data from the previous breath cycle
            self.dl.rotation_newfile()     # And Check whether we run out of space for the logger

    def _PID_update(self, dt):
        """
        This instantiates the PID control algorithms.
        During the breathing cycle, it goes through the four states:
           1) Rise to PIP, speed is controlled by flow (variable: `__SET_PIP_GAIN`)
           2) Sustain PIP pressure
           3) Quick fall to PEEP
           4) Sustaint PEEP pressure
        Once the cycle is complete, it checks the cycle for any alarms, and starts a new one.
        A record of pressure/volume waveforms is kept and saved

        Args:
            dt (float): timesstep since last update
        """

        now = time.time()
        cycle_phase = now - self._cycle_start
        next_cycle = False
        if len(self._flow_list) == self._BASELINE_ESTIMATOR_LENGTH:  # estimate the baseline flow during expiration with a rankfilter
            Qbaseline = np.percentile(self._flow_list, 5 )
        else:
            Qbaseline = 0
        self._DATA_VOLUME += dt * (self._DATA_Qout - Qbaseline)      # Integrate the flow-out to estimate VTE
        self._DATA_PRESSURE = np.median(self._DATA_PRESSURE_LIST)    # Catch some of the noise, if any.

        if cycle_phase < self.__SET_I_PHASE:
            self.__KP = 2.0*(self.__SET_PIP_GAIN-1)
            self.__KI = 2
            self.__KD = 0

            self.__get_PID_error(yis = self._DATA_PRESSURE, ytarget = self.__SET_PIP, dt = dt, RC = 0.3)
            self.__calculate_control_signal_in(dt = dt)
            self.__control_signal_out = 0

        elif cycle_phase < self.__SET_PEEP_TIME + self.__SET_I_PHASE:                                     # then, we drop pressure to PEEP
            self._flow_list.append(self._DATA_Qout )                                                      # Keep a list of the flow out of the lung; for baseline e stimation
            self.__control_signal_in = 0
            self.__control_signal_out = 1


        elif cycle_phase < self.__SET_CYCLE_DURATION:
            self._flow_list.append(self._DATA_Qout )
            self.__control_signal_out = 1
            self.__control_signal_in = 5 *(1 - np.exp( 5*((self.__SET_PEEP_TIME + self.__SET_I_PHASE) - cycle_phase )) )  # Make this nice and smooth.


            if self.breath_detection and (self._DATA_PRESSURE < self.__SET_PEEP - self.breath_pressure_drop):  #breath!
                self.logger.info("Autonomous breath detected; starting next cycle.")
                self._cycle_start = time.time()  # New cycle starts
                self._DATA_VOLUME = 0            # ... start at zero volume in the lung
                self._DATA_dpdt    = 0            # and restart the rolling average for the dP/dt estimation
                next_cycle = True

        else:
            self._cycle_start = time.time()  # New cycle starts
            self._DATA_VOLUME = 0            # ... start at zero volume in the lung
            self._DATA_dpdt    = 0            # and restart the rolling average for the dP/dt estimation
            next_cycle = True

        self.__test_for_alarms()
        if next_cycle:                        # if a new breath cycle has started
            self.__start_new_breathcycle()
        else:
            self.__cycle_waveform = np.append(self.__cycle_waveform, [[cycle_phase, self._DATA_PRESSURE, self._DATA_VOLUME]], axis=0)
        if self._save_logs:
            self.__save_values()

    def __save_values(self):
        """
        Helper function to reorganize key parameters in the main PID control loop, into a `SensorValues` object,
        that can be stored in the logfile, using a method from the DataLogger.
        """
        sensor_values =  SensorValues(vals={
        ValueName.PIP.name                  : self._DATA_PIP,
        ValueName.PEEP.name                 : self._DATA_PEEP,
        ValueName.FIO2.name                 : self.COPY_DATA_OXYGEN,
        ValueName.PRESSURE.name             : self._DATA_PRESSURE,
        ValueName.VTE.name                  : self._DATA_VTE,
        ValueName.BREATHS_PER_MINUTE.name   : self._DATA_BPM,
        ValueName.INSPIRATION_TIME_SEC.name : self._DATA_I_PHASE,
        ValueName.FLOWOUT.name              : self._DATA_Qout,
        'timestamp'                         : time.time(),
        'loop_counter'                      : self._loop_counter,
        'breath_count'                      : self._DATA_BREATH_COUNT
        })

        #And the control value instance
        control_values = ControlValues(
            control_signal_in = self.__control_signal_in,
            control_signal_out = self.__control_signal_out,
        )

        #And save both
        self.dl.store_waveform_data(sensor_values, control_values)

    def get_past_waveforms(self):
        """
        Public method to return a list of past waveforms from `__cycle_waveform_archive`.
        Note: After calling this function, archive is emptied! The format is
            - Returns a list of [Nx3] waveforms, of [time, pressure, volume]
            - Most recent entry is waveform_list[-1]

        Returns:
            list: [Nx3] waveforms, of [time, pressure, volume]
        """

        with self._lock:
            archive = list( self.__cycle_waveform_archive ) # Make sure to return a copy as a list
            self.__cycle_waveform_archive = deque(maxlen = self._RINGBUFFER_SIZE)
            self.__cycle_waveform_archive.append(archive[-1])
        self._time_last_contact = time.time()
        return archive

    def _start_mainloop(self):        # pragma: no cover
        """
        Prototype method to start main PID loop. Will depend on simulation or device, specified below.
        """
        pass   

    def start(self):
        """
        Method to start `_start_mainloop` as a thread.
        """
        self._time_last_contact = time.time()
        if self.__thread is None or not self.__thread.is_alive():  # If the previous thread has been stopped, make a new one.
            self._running.set()
            self.__thread = threading.Thread(target=self._start_mainloop, daemon=True)
            self.__thread.start()
        else:
            print("Main Loop already running.")

    def stop(self):
        """
        Method to stop the main loop thread, and close the logfile.
        """
        self._time_last_contact = time.time()
        if self.__thread is not None and self.__thread.is_alive():
            self._running.clear()
        else:
            print("Main Loop is not running.")

        if self._save_logs:               # If we kept records, flush the data
            self.dl.close_logfile()

    def is_running(self):
        """
        Public Method to assess whether the main loop thread is running.

        Returns:
            bool: Return true if and only if the main thread of controller is running.
        """
        self._time_last_contact = time.time()
        # TODO: this should be better thread-safe variable
        return self._running.is_set()

    def get_heartbeat(self):
        """
        Returns an independent heart-beat of the controller, i.e. the internal loop counter incremented in `_start_mainloop`.

        Returns:
            int: exact value of `self._loop_counter`
        """
        self._time_last_contact = time.time()
        return self._loop_counter

class ControlModuleDevice(ControlModuleBase): 
    """
    Uses ControlModuleBase to control the hardware.
    """
    # Implement ControlModuleBase functions
    def __init__(self, save_logs = True, flush_every = 10, config_file = None):
        """
        Initializes the ControlModule for the physical system. Inherits methods from ControlModuleBase

        Args:
            save_logs (bool, optional): Should logs be kept? Defaults to True.
            flush_every (int, optional): How often are log-files to be flushed, in units of main-loop-itertions? Defaults to 10.
            config_file (str, optional): Path to device config file, e.g. 'pvp/io/config/dinky-devices.ini'. Defaults to None.
        """
        ControlModuleBase.__init__(self, save_logs, flush_every)

        # Handler for HAL timeout handler for the timeout
        def handler(signum, frame):
            print("TIMEOUT - HAL not initialized")
            self.logger.warning("TIMEOUT - HAL not initialized. Using MockHAL")
            with pytest.raises( Exception ):
                raise Exception("HAL timeout")

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(5)

        try:
            self.HAL = io.Hal(config_file)
        except Exception: 
            self.HAL = HALMock() 
            #TODO: Raise technical alert

        self._sensor_to_COPY()

        # Current settings of the valves to avoid unneccesary hardware queries
        self.current_setting_ex = self.HAL.setpoint_ex
        self.current_setting_in = self.HAL.setpoint_in

    def __del__(self):
        """
        Destructor for the ControlModuleDevice class. Resets valves to standby, and closes log-files (via `ControlModuleBase`)
        """
        self.set_valves_standby()           # First set valves to default
        ControlModuleBase.__del__(self)     # and del the base

    def _sensor_to_COPY(self):
        """
        Copies the current measurements to`COPY_sensor_values`, so that it can be queried
        from the outside.
        """
        self._get_HAL() #Update sensor measurements

        with self._lock:
          self.COPY_sensor_values = SensorValues(vals={
              ValueName.PIP.name                  : self._DATA_PIP,
              ValueName.PEEP.name                 : self._DATA_PEEP,
              ValueName.FIO2.name                 : self.COPY_DATA_OXYGEN,
              ValueName.PRESSURE.name             : self._DATA_PRESSURE,
              ValueName.VTE.name                  : self._DATA_VTE,
              ValueName.BREATHS_PER_MINUTE.name   : self._DATA_BPM,
              ValueName.INSPIRATION_TIME_SEC.name : self._DATA_I_PHASE,
              ValueName.FLOWOUT.name              : self._DATA_Qout,
              'timestamp'                         : time.time(),
              'loop_counter'                      : self._loop_counter,
              'breath_count'                      : self._DATA_BREATH_COUNT
          })
            
    # @timeout  #TODO: find a save setting for timeout, as the hardware is kinda slow. >10ms?
    def _set_HAL(self, valve_open_in, valve_open_out):
        """
        Set Controls with HAL, decorated with a timeout.

        As hardware communication is the speed bottleneck. this code is slightly optimized in so far as only changes are sent to hardware.

        Args:
            valve_open_in (float): setting of the inspiratory valve; should be in range [0,100]
            valve_open_out (float): setting of the expiratory valve; should be 1/0 (open and close)
        """
        if self.current_setting_in is not max(min(100, int(valve_open_in)), 0):
            self.HAL.setpoint_in = max(min(100, int(valve_open_in)), 0)
            self.current_setting_in = max(min(100, int(valve_open_in)), 0)

        if self.current_setting_ex is not valve_open_out:
            self.current_setting_ex = valve_open_out
            self.HAL.setpoint_ex =  valve_open_out

    # @timeout
    def _get_HAL(self):
        """
        Get sensor values from HAL, decorated with timeout.
        As hardware communication is the speed bottleneck. this code is slightly optimized in so far as some sensors are
        queried only in certain phases of the breatch cycle. This is done to run the primary PID loop as fast as possible:

            - pressure is always queried
            - Flow is queried only outside of inspiration
            - In addition, oxygen is only read every 5 seconds.

        """
        inspiration_phase = (time.time() - self._cycle_start) < self.COPY_SET_I_PHASE

        self._DATA_PRESSURE_LIST.append( self.HAL.pressure )             # Append pressure to list -> is averaged over a couple values

        if inspiration_phase:
            self._DATA_Qout         = 0                                  # Flow out and oxygen are not measured
            self.COPY_DATA_OXYGEN   = self._DATA_OXYGEN
        else:
            if time.time() - self._OXYGEN_LAST_READ > 5:                 # If the time has come, get an oxygen value.
                self._DATA_OXYGEN = self.HAL.oxygen
                self._OXYGEN_LAST_READ = time.time()

            self._DATA_Qout = self.HAL.flow_ex/60                        # Get a flow reading in l/sec


    def set_valves_standby(self):
        """
        This returns valves back to normal setting (in: closed, out: open)
        """
        self.logger.info('Valves to stand-by.')
        self._set_HAL(valve_open_in = 0, valve_open_out = 1)  # Defined state to make sure that it does not pop up.

    def _start_mainloop(self):
        """
        This is the main loop. This method should be run as a thread (see the `start()` method in `ControlModuleBase`)
        """
        self.logger.info('MainLoop: start')
        self._last_update = time.time()

        update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE

        try:
            while self._running.is_set():
                self._loop_counter += 1
                now = time.time()
                dt = now - self._last_update                            # Time sincle last cycle of main-loop

                if dt > CONTROL[ValueName.BREATHS_PER_MINUTE].default / 4:                                                      # TODO: RAISE HARDWARE ALARM, no update should be so long
                    self.logger.warning("MainLoop: Update too long: " + str(dt))
                    print("Restarted cycle.")
                    self._control_reset()
                    dt = self._LOOP_UPDATE_TIME

                self._get_HAL()                                          # Update pressure and flow measurement
                self._PID_update(dt = dt)                            # With that, calculate controls
                valve_open_in  = self._get_control_signal_in()           #    -> Inspiratory side: get control signal for PropValve
                valve_open_out = self._get_control_signal_out()          #    -> Expiratory side: get control signal for Solenoid
                self._set_HAL(valve_open_in, valve_open_out)             # And set values.

                self._last_update = now

                if update_copies == 0:
                    self._controls_from_COPY()     # Update controls from possibly updated values as a chunk
                    self._sensor_to_COPY()         # Copy sensor values to COPY
                    update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
                else:
                    update_copies -= 1

                if self._LOOP_UPDATE_TIME > 0:
                    time.sleep(self._LOOP_UPDATE_TIME)

        # # get final values on stop
        finally:
            self._controls_from_COPY()  # Update controls from possibly updated values as a chunk
            self._sensor_to_COPY()  # Copy sensor values to COPY
            self.set_valves_standby()

class HALMock():
    """
    A HAL mock class to fall back to, if io.HAL times out. Unclear what the software is to do, if hardware is available...
    Decision: Start up with a technical alert.
    """
    def __init__(self):
        self.setpoint_in = 0
        self.setpoint_ex = 0
        self.pressure    = 0
        self.oxygen      = 0
        self.flow_ex     = 0

class Balloon_Simulator:
    """
    Physics simulator for inflating a balloon with an attached PEEP valve.
    For math, see https://en.wikipedia.org/wiki/Two-balloon_experiment
    """

    def __init__(self, peep_valve):
        # Hard parameters for the simulation
        self.max_volume = 6    # Liters  - 6?
        self.min_volume = 1.5  # Liters - baloon starts slightly inflated.
        self.PC = 50           # Proportionality constant that relates pressure to cm-H2O
        self.P0 = 0            # Baseline/Minimum pressure.
        self.leak = True

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
        self.peep_valve = peep_valve

    def get_pressure(self):
        return self.current_pressure

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
        conductance = 0.01*Qout_clip                     # This should be in the range of ~1 liter/s for typical max pressure differences
        if self.current_pressure > self.peep_valve:      # Action of the PEEP valve
            self.Qout = difference_pressure * conductance    # Target for flow out
        else:
            self.Qout = 0

    def update(self, dt):  # Performs an update of duration dt [seconds]

        if dt<1:                                         # This is the simulation, so not quite so important, but no update should take longer than that
            self.current_flow = self.Qin - self.Qout     # Flow into the balloon is the difference between flow-in and flow-out of the system
            self.current_volume += self.current_flow * dt

            # This is from the baloon equation, uses helper variable (the baloon radius)
            self.r_real = (3 * self.current_volume / (4 * np.pi)) ** (1 / 3)
            r0 = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)

            new_pressure = self.P0 + (self.PC / (r0 ** 2 * self.r_real)) * (1 - (r0 / self.r_real) ** 6)
            self.current_pressure = new_pressure

            # o2 fluctuations modelled as OUprocess
            self.fio2 = self.OUupdate(self.fio2, dt=dt, mu=60, sigma=5, tau=1)
        else:
            self._reset()


    def OUupdate(self, variable, dt, mu, sigma, tau):
        """
        This is a simple function to produce an OU process on `variable`.
        It is used as model for fluctuations in measurement variables.

        Args:
            variable (float): value of a variable at previous time step
            dt (float): timestep
            mu (float)): mean
            sigma (float): noise amplitude
            tau (float): time scale

        Returns:
            float: value of "variable" at next time step
        """
        dt = max(dt, 0.05)  # Make sure this doesn't go haywire if anything hangs. Max 50ms
        sigma_bis = sigma * np.sqrt(2. / tau)
        sqrtdt = np.sqrt(dt)
        new_variable = variable + dt * (-(variable - mu) / tau) + sigma_bis * sqrtdt * np.random.randn()
        return new_variable

    def _reset(self):
        """
        Resets Balloon to default settings.
        """
        self.set_Qin          = 0
        self.Qin              = 0
        self.set_Qout         = 0
        self.Qout             = 0
        self.current_pressure = 0
        self.r_real = (3 * self.min_volume / (4 * np.pi)) ** (1 / 3)
        self.current_volume = self.min_volume

class ControlModuleSimulator(ControlModuleBase):
    """
    Controlling Simulation.
    """
    # Implement ControlModuleBase functions
    def __init__(self, save_logs: bool = False, simulator_dt = None, peep_valve_setting = 5):
        """
        Initializes the ControlModuleBase with the simple simulation (for testing/dev).

        Args:
            save_logs (bool, optional): should logs be saved? (Useful for testing)
            simulator_dt (float, optional): timestep between updates. Defaults to None.
            peep_valve_setting (int, optional): Simulates action of a PEEP valve. Pressure cannot fall below. Defaults to 5.
        """
        ControlModuleBase.__init__(self, save_logs = False)
        self.Balloon = Balloon_Simulator(peep_valve = peep_valve_setting)          # This is the simulation
        self._sensor_to_COPY()
        self._LOOP_UPDATE_TIME = prefs.get_pref('CONTROLLER_LOOP_UPDATE_TIME_SIMULATOR')

        self.simulator_dt = simulator_dt

    def __del__(self):
        ControlModuleBase.__del__(self)

    def __SimulatedPropValve(self, x):
        """
        This simulates the action of a proportional valve.
        Flow-current-curve eye-balled from generic prop vale with logistic activation.

        Args:
            x (float): A control variable [like pulse-width-duty cycle or mA]

        Returns:
            float: flow through the valve
        """
        flow_new = (np.tanh(0.12*(x - 30)) + 1)
        if x<0:
            flow_new = 0
        return flow_new

    def __SimulatedSolenoid(self, x):
        """
        This simulates the action of a two-state Solenoid valve.

        Args:
            x (float): If x==0: valve closed; x>0: flow set to "1"

        Returns:
            float: current flow
        """
        if x > 0:
            return 1.
        else:
            return 0.

    def _sensor_to_COPY(self):
        """
        Make the sensor value object from current (simulated) measurements
        """
        with self._lock:
            self.COPY_sensor_values = SensorValues(vals={
              ValueName.PIP.name                  : self._DATA_PIP,
              ValueName.PEEP.name                 : self._DATA_PEEP,
              ValueName.FIO2.name                 : self.Balloon.fio2,
              ValueName.PRESSURE.name             : self.Balloon.current_pressure,
              ValueName.VTE.name                  : self._DATA_VTE,
              ValueName.BREATHS_PER_MINUTE.name   : self._DATA_BPM,
              ValueName.INSPIRATION_TIME_SEC.name : self._DATA_I_PHASE,
              ValueName.FLOWOUT.name              : self._DATA_Qout,
              'timestamp'                         : time.time(),
              'loop_counter'                      : self._loop_counter,
              'breath_count'                      : self._DATA_BREATH_COUNT
            })

    def _start_mainloop(self):
        """
        This is the main loop. This method should be run as a thread (see the `start()` method in `ControlModuleBase`)
        """
        update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
        self.logger.info("MainLoop: start")
        while self._running.is_set():
            self._loop_counter += 1
            now = time.time()
            if self.simulator_dt:
                dt = self.simulator_dt
            else:
                dt = now - self._last_update                            # Time sincle last cycle of main-loop
                # if dt > 0.2:                                            # TODO: RAISE HARDWARE ALARM, no update should take longer than 0.5 sec
                #     self.logger.warning("MainLoop: Update too long: " + str(dt))
                #     print("Restarted cycle.")
                #     self._control_reset()
                #     self.Balloon._reset()
                #     dt = self._LOOP_UPDATE_TIME

            self.Balloon.update(dt = dt)                            # Update the state of the balloon simulation
            self._DATA_PRESSURE_LIST.append(self.Balloon.get_pressure()) # Get a pressure measurement from balloon and tell controller

            self._PID_update(dt = dt)                               # Update the PID Controller

            x = self._get_control_signal_in()                       # Inspiratory side: get control signal for PropValve
            Qin = self.__SimulatedPropValve(x)                      # And calculate the produced flow Qin

            y = self._get_control_signal_out()                      # Expiratory side: get control signal for Solenoid
            Qout = self.__SimulatedSolenoid(y)                      # Set expiratory flow rate, Qout

            self.Balloon.set_flow_in(Qin, dt = dt)                  # Set the flow rates for the Balloon simulator
            self.Balloon.set_flow_out(Qout, dt = dt)

            self._DATA_Qout = self.Balloon.Qout                     # Tell controller the expiratory flow rate, _DATA_Qout
            self.COPY_DATA_OXYGEN = self.Balloon.fio2               # And for logging the simulatede O2 concentration

            self._last_update = now

            if update_copies == 0:
                self._controls_from_COPY()     # Update controls from possibly updated values as a chunk
                self._sensor_to_COPY()         # Copy sensor values to COPY
                update_copies = self._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE
            else:
                update_copies -= 1
            if self._LOOP_UPDATE_TIME > 0:
                time.sleep(self._LOOP_UPDATE_TIME)

        # get final values on stop
        self._controls_from_COPY()  # Update controls from possibly updated values as a chunk
        self._sensor_to_COPY()  # Copy sensor values to COPY




def get_control_module(sim_mode=False, simulator_dt = None):
    """
    Generates control module.

    Args:
        sim_mode (bool, optional): if ``true``: returns simulation, else returns hardware. Defaults to False.
        simulator_dt (float, optional): a timescale for thee simulation. Defaults to None.

    Returns:
        ControlModule-Object: Either configured for simulation, or physical device.
    """
    if sim_mode == True:
        return ControlModuleSimulator(save_logs = True, simulator_dt = simulator_dt)
    else:
        return ControlModuleDevice(save_logs = True, flush_every = 1, config_file = 'pvp/io/config/devices.ini')
