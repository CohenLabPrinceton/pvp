from .iobase import i2cDevice
from time import sleep

''' Class definitions for Analog to Digital Converters (ADCs), Digital to Analog Converters (DACs), and the like
'''

class ads1115(i2cDevice):  
    ''' Description:
    Class for the ADS1115 16 bit, 4 Channel ADC.
    Datasheet:
     http://www.ti.com/lit/ds/symlink/ads1114.pdf?ts=1587872241912
        
    Default Values: 
     Default configuration for vent:     0xC3E3
     Default configuration on power-up:  0x8583
    '''
    _DEFAULT_ADDRESS        = 0x48
    _DEFAULT_VALUES         = {'MUX':0, 'PGA':4.096, 'MODE':'SINGLE', 'DR':860}
    
    ''' Address Pointer Register (write-only) '''
    _POINTER_FIELDS = ( 'P' )
    _POINTER_VALUES = ( ('CONVERSION', 'CONFIG', 'LO_THRESH', 'HIGH_THRESH'), )
    
    ''' Config Register (R/W) '''
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
                        
    ''' Note:
    The Conversion Register is read-only and contains a 16bit representation of 
    the requested value (provided the conversion is ready).
    The Lo-thresh & Hi-thresh Registers are not used in this application.
    However, their function and usage are described in the datasheet. 
    '''
    
    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        super().__init__(address,i2c_bus,pig)
        ''' Initializes registers: Pointer register is write only, 
        config is R/W. Sets initial value of _last_cfg to what is
        actually on the ADS.Packs default settings into _cfg, but does
        not actually write to ADC - that occurs when read() is called.
        '''
        self.pointer    = self.Register(self._POINTER_FIELDS,self._POINTER_VALUES)
        self._config    = self.Register(self._CONFIG_FIELDS,self._CONFIG_VALUES)
        self._last_cfg  = self._read_last_cfg()
        self._cfg       = self._config.pack(cfg  = self._last_cfg,
											MUX  = self._DEFAULT_VALUES['MUX'],
											PGA  = self._DEFAULT_VALUES['PGA'],
											MODE = self._DEFAULT_VALUES['MODE'],
											DR   = self._DEFAULT_VALUES['DR'] )
                                            
    def read(self,channel=None,gain=None,mode=None,data_rate=None):
        ''' Returns a voltage (expressed as a float) corresponding to a
        channel on the ADC. The channel to read from, along with the
        gain, mode, and sample rate of the conversion may be may be
        specified as optional parameters. If read() is called with no
        parameters, the resulting voltage corresponds to the channel
        last read from and the same conversion settings.
        '''
        return self._read(  channel=channel,
                            gain=gain,
                            mode=mode,
                            data_rate=data_rate) * self._config.PGA.unpack(self._cfg) / 32767

    @property
    def config(self):
        ''' Returns the human-readable configuration for the next read.    
        '''
        return self._config.unpack(self._cfg)

    @property
    def cfg(self):
        ''' Returns the contents (as a 16-bit unsigned integer) of the 
        configuration that will be written to the config register when
        read() is next called.
        '''
        return self._cfg

    def _read(self,channel=None,gain=None,mode=None,data_rate=None):
        ''' Backend for read(). Returns the contents of the 16-bit
        conversion register as an unsigned integer.
        
        If no parameters are passed, one of two things can happen:
        
            1)  If the ADC is in single-shot (mode='SINGLE') conversion 
                mode, _last_cfg is written to the config register; once 
                the ADC indicates it is ready, the contents of the 
                conversion register are read and the result is returned.  
            2)  If the ADC is in CONTINUOUS mode, the contents of the
                conversion register are read immediately and returned.
                
        If any of channel, gain, mode, or data_rate are specified as 
        parameters, a new _cfg is packed and written to the config
        register; once the ADC indicates it is ready, the contents of 
        the conversion register are read and the result is returned. 
                
        Note: In continuous mode, data can be read from the conversion
        register of the ADS1115 at any time and always reflects the
        most recently completed conversion. So says the datasheet.
        '''
        self._cfg = self._config.pack(  cfg  = self._cfg,
                                        MUX  = channel,
                                        PGA  = gain,
                                        MODE = mode,
                                        DR   = data_rate)
        mode = self._config.MODE.unpack(self._cfg)
        if self._cfg != self._last_cfg or mode == 'SINGLE':
            self.write_register(self.pointer.P.pack('CONFIG'), self._cfg)
            self._last_cfg  = self._cfg
            data_rate = self._config.DR.unpack(self._cfg)
            while not ( self._ready() or  mode == 'CONTINUOUS' ):
                tick = self._pig.get_current_tick()
                while ((self._pig.get_current_tick() - tick) < 1000000/data_rate):
                    pass
        return self.read_register(self.pointer.P.pack('CONVERSION'))

    def _read_last_cfg(self):
        ''' Reads the config register and returns the contents as a
        16-bit unsigned integer; updates internal record _last_cfg. 
        '''
        self._last_cfg = self.read_register(self.pointer.P.pack('CONFIG'))
        return self._last_cfg
        
    def _ready(self):
        ''' Return status of ADC conversion. '''
        # OS = 0: Device is currently performing a conversion
        # OS = 1: Device is not currently performing a conversion
        return self.read_register(self.pointer.P.pack('CONFIG')) >> 15
