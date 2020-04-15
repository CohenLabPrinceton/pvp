# library imports:
import time
import gpiozero
from sensors import JuliePlease
#import RPi.GPIO as GPIO   # Import the GPIO library.

class ControlSettings:
# A class for obtaining sensor readings at a single timepoint. 
    def __init__(self):
        self.pip = 35.0       # PIP (peak inspiratory pressure) value, in cm H20
        self.peep = 5.0       # PEEP (positive-end expiratory pressure) value, in cm H20
        self.insptime = 1.5   # Inspiratory time, in seconds
        self.breathrate = 20  # Breath rate, in beats per minute
        self.vt = 500         # Tidal volume, in mL
        self.SAMPLETIME = 0.01

    def reset(self):
        self._state = 0
        self.pip = 35.0       # PIP (peak inspiratory pressure) value, in cm H20
        self.peep = 5.0       # PEEP (positive-end expiratory pressure) value, in cm H20
        self.insptime = 1.5   # Inspiratory time, in seconds
        self.breathrate = 20  # Breath rate, in beats per minute
        self.vt = 500         # Tidal volume, in mL
        self.SAMPLETIME = 0.01

class Controller:
    # This is to be the brains of the operation
    def __init__(self,jp,logger):
        # Initlize sensor interface, datalogger, & controller settings
        self.jp     = jp
        self.logger = logger
        self.settings = ControlSettings()
        # Sets up the GPIO interface for valve control.
        self.inlet = gpiozero.DigitalOutputDevice(17, active_high=True, initial_value=True) #starts open
        self.inspir = gpiozero.PWMOutputDevice(22, active_high=True, initial_value=0, frequency = 20) #starts closed
        self.expir = gpiozero.DigitalOutputDevice(27, active_high=False, initial_value=True) #Starts open
        # Initialize control state (assume I.C. is inhale) 
        self._state = 0
        self.__inhale()
        # Keep's track of how long each state lasts
        self.state_time = time.time()

    def gpio_cleanup(self):
        # Powers off pins and cleans up GPIO after run is terminated. 
        self.inlet.close()
        self.inspir.close()
        self.expir.close()
        
    def get_state(self):
        return self._state
    
    def __inc_state(self):
        self._state = (self._state + 1) % 4
    
    def __del__(self):
        self.gpio_cleanup()

    def update(self):
        # Updates valve controller using sensor readings and control settings. 
        # Should also log prior controller commands (not implemented).
    # Control scheme assumes the use of a PEEP valve
        assert(self.inlet.value == True),"Inlet valve should be open!"
        self.logger.update()
        self.__print_status()
        # change the following to grabbing last observations from logger
        if(self._state==0):
            # INHALING
            # Inlet flow is open, expiratory dump valve closed
            if(self.jp.get_pressure(1) > self.settings.pip):
                self.__hold_pip()
        elif(self._state==1):
            # Maintaining inspiratory plateau.
            # All valves closed.
            elapsed = time.time() - self.start_time
            if(elapsed > self.settings.insptime):
                self.__exhale()
        elif(self._state==2):
            # EXHALING
            # Open expiratory valve and dump pressure.
            if(self.jp.get_pressure(1) < self.settings.peep): 
                self.__hold_peep()
        elif(self._state==3):
            # AT REST 
            # Open inspiratory valve and maintain PEEP level w/PEEP valve.
            elapsed = time.time() - self.start_time
            if(elapsed > 60/self.settings.breathrate):
                self.__inhale()
        
    def __inhale(self):
        self.start_time = time.time()
        self.inspir.on()
        self.expir.off()
        self.__inc_state()
        
    def __hold_pip(self):
        self.inspir.off()
        self.__inc_state()
        
    def __exhale(self):
        self.expir.on()
        self.__inc_state()
        
    def __hold_peep(self):
        self.expir.off()
        #self.inspir.on()
        self.logger.calculate_last_tv()
        self.__print_breath(self.logger.tv)
        self.__inc_state()
        
    def __print_status(self):
        # change this to grabbing last observations from logger
        print("STATE: %2d pressure_0: %4.1f pressure_1: %4.1f flow: %4.0f"%(self._state,self.jp.get_pressure(1),self.jp.get_pressure(1),self.jp.get_flow()))#,end="\r")
        print(self.jp.get_temperature())

    def __print_breath(self,tv):
        return
        # TODO -------------------------------------------------
        #print("\n Last breath: %2.1f seconds, %4.0f mL tidal volume"%(0,0))

class DataLogger:
# A class for keeping track of prior sensor values.
# These are used by controllers and to sound alarms.
    def __init__(self, jp):
        self.jp = jp
        self._track_len = 50    # Type int: How long to retain sensor data. Could vary this later per sensor. 
        self.pres1_track = []
        self.pres2_track = []
        self.o2_track = []
        self.flow_track = []
        self.temp_track = []
        self.humid_track = []
        self.tv     = []

    def update(self):
    # Takes in current sensor readings object; updates tracking log for all sensors.
        self.pres1_track = self.update_single_sensor(self.pres1_track, self.jp.get_pressure(0), self._track_len)
        self.pres2_track = self.update_single_sensor(self.pres2_track, self.jp.get_pressure(1), self._track_len)
        self.o2_track = self.update_single_sensor(self.o2_track, self.jp.get_o2(), self._track_len)
        self.flow_track = self.update_single_sensor(self.flow_track, self.jp.get_flow(), self._track_len)
        self.temp_track = self.update_single_sensor(self.temp_track, self.jp.get_temperature(), self._track_len)
        self.humid_track = self.update_single_sensor(self.humid_track, self.jp.get_humidity(), self._track_len)

    def calculate_last_tv(self):
        # integrate flow over the last breath
        # TODO -------------------------------------------------
        self.tv = -1
        return self.tv
    
    def reset(self):
        self.pres1_track = []
        self.pres2_track = []
        self.o2_track = []
        self.flow_track = []
        self.temp_track = []
        self.humid_track = []

    def update_single_sensor(self, track, val, track_len):
        # Adds newest sensor reading to end of track.
        # Only store most recent [track_len] values.
        
        # Check if list is already at max track length:
        if(len(track) >= track_len):
            # Remove first element
            track.pop(0)
        # Add current sensor reading to track:
        track.append(val)  
        return track 
