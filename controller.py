# library imports:
import time # not needed - for testing
import gpiozero
#import RPi.GPIO as GPIO   # Import the GPIO library.

class ControlSettings:
    # A class for obtaining sensor readings at a single timepoint. 
    def __init__(self):
        self.pip = 30.0       # PIP (peak inspiratory pressure) value, in cm H20
        self.peep = 5.0       # PEEP (positive-end expiratory pressure) value, in cm H20
        self.insptime = 1.5   # Inspiratory time, in seconds
        self.breathrate = 20  # Breath rate, in beats per minute
        self.vt = 500         # Tidal volume, in mL
                
    def reset(self):
        self.pip = 30.0       # PIP (peak inspiratory pressure) value, in cm H20
        self.peep = 5.0       # PEEP (positive-end expiratory pressure) value, in cm H20
        self.insptime = 1.5   # Inspiratory time, in seconds
        self.breathrate = 20  # Breath rate, in beats per minute
        self.vt = 500         # Tidal volume, in mL

class Controller:
    def __init__(self):
        # Sets up the GPIO interface for valve control.
        self.inlet = gpiozero.DigitalOutputDevice(17, active_high=True, initial_value=True) #starts open
        self.inspir = gpiozero.PWMOutputDevice(22, active_high=True, initial_value=0) #starts closed
        self.expir = gpiozero.DigitalOutputDevice(27, active_high=False, initial_value=True) #Starts open
        self.settings = ControlSettings()
   
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
        # Should also log prior controller commands.
        
        assert(self.inlet.value == True),"Inlet valve should be open!"
        
        pip = self.settings.pip
        peep = self.settings.peep

        self.inspir.on()
        self.expir.off()

        pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
        print(pr)
        if(pr > 40):
            self.inspir.off()
            time.sleep(1)
            self.expir.on()
            pr = jp.get_pressure2_reading()
            print(pr)
            while (pr > 5):
                pr = jp.get_pressure2_reading()
                print(pr)
            self.inspir.on()
            #self.expir.off()
            time.sleep(2)

        
        return


