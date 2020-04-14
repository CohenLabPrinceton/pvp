# library imports:
import time # not needed - for testing
#import RPi.GPIO as GPIO   # Import the GPIO library.

class ControlSettings:
    # A class for obtaining sensor readings at a single timepoint. 
    def __init__(self):
        self._state = 0
        self.pip = 35.0       # PIP (peak inspiratory pressure) value, in cm H20
        self.peep = 5.0       # PEEP (positive-end expiratory pressure) value, in cm H20
        self.insptime = 1.5   # Inspiratory time, in seconds
        self.breathrate = 20  # Breath rate, in beats per minute
        self.vt = 500         # Tidal volume, in mL
                
    def reset(self):
        self._state = 0
        self.pip = 35.0       # PIP (peak inspiratory pressure) value, in cm H20
        self.peep = 5.0       # PEEP (positive-end expiratory pressure) value, in cm H20
        self.insptime = 1.5   # Inspiratory time, in seconds
        self.breathrate = 20  # Breath rate, in beats per minute
        self.vt = 500         # Tidal volume, in mL
      
    def get_state(self):
        return self._state
    
    def inc_state(self):
        self._state = (self._state + 1) % 4
        return 
        

class Controller:
    def __init__(self):
        import gpiozero
        # Sets up the GPIO interface for valve control.
        self.inlet = gpiozero.DigitalOutputDevice(17, active_high=True, initial_value=True) #starts open
        self.inspir = gpiozero.PWMOutputDevice(22, active_high=True, initial_value=0, frequency = 20) #starts closed
        self.expir = gpiozero.DigitalOutputDevice(27, active_high=False, initial_value=True) #Starts open
        self.settings = ControlSettings()
        self.start_timer = time.time()
   
    def gpio_cleanup(self):
        # Powers off pins and cleans up GPIO after run is terminated. 
        self.inlet.close()
        self.inspir.close()
        self.expir.close()
        return
    
    def __del__(self):
        self.gpio_cleanup()
        return

    def update_controller(self, jp, tracker):
        # Updates valve controller using sensor readings and control settings. 
        # Should also log prior controller commands (not implemented).
        
        assert(self.inlet.value == True),"Inlet valve should be open!"
        
        state = self.settings.get_state()
        pip = self.settings.pip
        peep = self.settings.peep
        insp_time = self.settings.insptime
        vt = self.settings.vt
        
        rise_time = insp_time / 3.0
        rise_ticks = 5
        breath_time = (60.0 / self.settings.breathrate)
        exp_time = breath_time - insp_time
        
        if(state==0):
            # Rise to max pressure value.
            self.start_timer = time.time()
            self.inspir.on()
            self.expir.off()
            pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
            print(pr)
            if(pr > pip):
                self.settings.inc_state()
            print(state)
            
        elif(state==1):
            # Maintain inspiratory plateau.
            self.inspir.off()
            pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
            print(pr)
            elapsed = time.time() - self.start_timer
            if(elapsed > insp_time):
                self.settings.inc_state()
            print(state)
            
            
        elif(state==2):
            # Release expiratory valve and drop down to PEEP.
            self.expir.on()
            pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
            print(pr)
            if(pr < peep):
                self.settings.inc_state()
            print(state)
                
        elif(state==3):
            # Maintain PEEP level.
            self.expir.off()
            pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
            print(pr)
            elapsed = time.time() - self.start_timer
            if(elapsed > breath_time):
                self.settings.inc_state()
            print(state)
        
        return


