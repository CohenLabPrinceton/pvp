class Balloon_Simulator:
    '''
    This is a simulator for inflating a balloon. 
    For math, see https://en.wikipedia.org/wiki/Two-balloon_experiment

    However, to make the UI work, we need to wrap this with a class and use the interfaces here to coordinate those two components:
    https://docs.google.com/document/d/13eqc3OJCYJAI3sxCdSosR6H6VLpEPJxDEBhGktyFTHg/edit#

     It's easier if you could implement the implementations in the control part. The message types have been defined, but the messaging passing need to be implement.
    '''
    
    def __init__(self, leak, delay):
        #Hard parameters for the simulation
        self.max_volume       = 6     # Liters  - 6?
        self.min_volume       = 1.5   # Liters - baloon starts slightly inflated.
        self.PC               = 20    # Proportionality constant that relates pressure to cm-H2O 
        self.P0               = 0     # Minimum pressure.
        self.leak             = leak
        self.delay            = delay
        
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