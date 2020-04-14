# library imports:
import time # not needed - for testing
import controller


class ControllerSim(controller.Controller):
    def __init__(self):
        # Sets up the GPIO interface for valve control.
        self.settings = controller.ControlSettings()
        self.start_timer = time.time()
   
    def gpio_cleanup(self):
        # Powers off pins and cleans up GPIO after run is terminated. 
        return
    
    def __del__(self):
        return

    def update_controller(self, jp, tracker):
        # # Updates valve controller using sensor readings and control settings.
        # # Should also log prior controller commands (not implemented).
        #
        # assert(self.inlet.value == True),"Inlet valve should be open!"
        #
        # state = self.settings.get_state()
        # pip = self.settings.pip
        # peep = self.settings.peep
        # insp_time = self.settings.insptime
        # vt = self.settings.vt
        #
        # rise_time = insp_time / 3.0
        # rise_ticks = 5
        # breath_time = (60.0 / self.settings.breathrate)
        # exp_time = breath_time - insp_time
        #
        # if(state==0):
        #     # Rise to max pressure value.
        #     self.start_timer = time.time()
        #     self.inspir.on()
        #     self.expir.off()
        #     pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
        #     print(pr)
        #     if(pr > pip):
        #         self.settings.inc_state()
        #     print(state)
        #
        # elif(state==1):
        #     # Maintain inspiratory plateau.
        #     self.inspir.off()
        #     pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
        #     print(pr)
        #     elapsed = time.time() - self.start_timer
        #     if(elapsed > insp_time):
        #         self.settings.inc_state()
        #     print(state)
        #
        #
        # elif(state==2):
        #     # Release expiratory valve and drop down to PEEP.
        #     self.expir.on()
        #     pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
        #     print(pr)
        #     if(pr < peep):
        #         self.settings.inc_state()
        #     print(state)
        #
        # elif(state==3):
        #     # Maintain PEEP level.
        #     self.expir.off()
        #     pr = jp.get_pressure2_reading()       # Returns current pressure reading in cmH2O
        #     print(pr)
        #     elapsed = time.time() - self.start_timer
        #     if(elapsed > breath_time):
        #         self.settings.inc_state()
        #     print(state)
        #
        return


