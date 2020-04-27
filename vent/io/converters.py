from iobase import i2cDevice
from time import sleep

'''
Class definitions for Analog to Digital Converters (ADCs), Digital to Analog Converters (DACs), and the like
'''

class ads1115(i2cDevice):  
    '''
    Class for the ADS1115 16 bit, 4 Channel ADC.
    Datasheet:
        http://www.ti.com/lit/ds/symlink/ads1114.pdf?ts=1587872241912
    '''
    
    '''Default Values'''
    #Default ventidude config:   '0b1100001111100011' / 0xC3E3 / 50147
    #Default config on power-up: '0b1000010110000101' / 0x8583 / 34179
    _DEFAULT_ADDRESS        = 0x48
    _DEFAULT_VALUES         = {'MUX':0, 'PGA':4.096, 'MODE':'SINGLE', 'DR':860}
    
    '''Address Pointer Register (write-only)'''
    _POINTER_FIELDS = ( 'P' )
    _POINTER_VALUES = ( ('CONVERSION', 'CONFIG', 'LO_THRESH', 'HIGH_THRESH'), )
    
    '''Config Register (R/W) '''
    _CONFIG_FIELDS = ('OS','MUX','PGA','MODE','DR','COMP_MODE','COMP_POL','COMP_LAT','COMP_QUE')   
    _CONFIG_VALUES  = ( ( 'NO_EFFECT', 'START_CONVERSION' ),
                        ( (0, 1), (0, 3), (1, 3), (2, 3), 0, 1, 2, 3 ),
                        ( 6.144, 4.096, 2.048, 1.024, 0.512, 0.256, 0.256, 0.256 ),
                        ( 'CONTINUOUS', 'SINGLE' ),
                        ( 8, 16, 32, 64, 128, 250, 475, 860 ),
                        ( 'TRADIONAL', 'WINDOW' ),
                        ( 'ACTIVE_LOW', 'ACTIVE_HIGH' ),
                        ( 'NONLATCHING', 'LATCHING' ),
                        ( 1, 2, 3, 'DISABLE' ) )
                        
    '''
    Note: The Conversion Register is read-only and contains a 16bit representation of 
    the requested value (provided the conversion is ready).
    The Lo-thresh & Hi-thresh Registers are not used in this application.
    However, their function and usage are described in the datasheet. 
    '''
    
    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None,):
        super().__init__(address,i2c_bus,pig)
        '''Define registers. Pointer register is write only, config is R/W.'''
        self.pointer    = self.Register(self._POINTER_FIELDS,self._POINTER_VALUES)
        self.config     = self.Register(self._CONFIG_FIELDS,self._CONFIG_VALUES)
        '''Set initial value of _LAST_CFG to what is actually on the ADS'''
        self._LAST_CFG  = self.read_register(self.pointer.P.pack('CONFIG'))
        '''Pack default settings into _CFG, don't bother to write to ADC yet'''
        self._CFG       = self.config.pack( cfg     = self._LAST_CFG,
                                            MUX     = self._DEFAULT_VALUES['MUX'],
                                            PGA     = self._DEFAULT_VALUES['PGA'],
                                            MODE    = self._DEFAULT_VALUES['MODE'],
                                            DR      = self._DEFAULT_VALUES['DR'] )
                                            
    def read(self,channel=None,gain=None,mode=None,data_rate=None):
        '''Performs a raw_read and converts the result to voltage '''
        return self.raw_read(channel=channel,gain=gain,mode=mode,data_rate=data_rate)*self.config.PGA.unpack(self._CFG) / 32767
    
    def raw_read(self,channel=None,gain=None,mode=None,data_rate=None):
        '''
        Packs any new values passed as arguments into a new cfg. 
        If new cfg differs from the last, or if single-shot mode is specified,
        write new cfg to config register and wait for conversion.
        Otherwise, or after the above has been done, read the conversion value.
        '''
        self._CFG = self.config.pack(self._CFG,MUX=channel,PGA=gain,MODE=mode,DR=data_rate)
        mode = self.config.MODE.unpack(self._CFG)
        if self._CFG != self._LAST_CFG or mode == 'SINGLE':
            self.write_register(self.pointer.P.pack('CONFIG'), self._CFG)
            sleep(1/self.config.DR.unpack(self._CFG))
            while not ( self.ready() or  mode == 'CONTINUOUS' ):
                sleep(1/self.config.DR.unpack(self._CFG)/10)
                #pass       # not sure which is better here
        self._LAST_CFG = self._CFG
        return self.read_register(self.pointer.P.pack('CONVERSION'))
    
    def ready(self):
        '''Return status of ADC conversion.'''
        # OS = 0: Device is currently performing a conversion
        # OS = 1: Device is not currently performing a conversion
        return self.read_register(self.pointer.P.pack('CONFIG')) & (1 << self.config.OS.offset())
