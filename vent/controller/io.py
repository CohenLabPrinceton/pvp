import pigpio
import abc
import numpy as np
from collections import OrderedDict
from time import sleep

class Ventilator:
    '''
    Class representation of the physical ventilator device
    '''
    def __init__(self):
        self.pig = pigpio.pi()
	
    def __del__(self):
        self.pig.stop()

    def test(self,sensor):
        return result

    def calibrate(self):
        return


class Device(abc.ABC):
    '''
    Abstract class for pigpio handles
    '''
    def __init__(self,pig):
        self._pig = pig if pig is not None else pigpio.pi()

    def __del__(self):
        self.close()

    @property
    def handle(self):
        return self._handle

    def close(self):
        self._pig.close(self._handle)

class i2cDevice(Device):
    '''
    A class wrapper for pigpio I2C handles 
    '''
    def __init__(self, i2c_address, i2c_bus, pig=None):
        super().__init__(pig)
        self._handle    = self._pig.i2c_open(i2c_bus,i2c_address)

    def read_device(self,num_bytes):
        '''
        Read a specified number of bytes directly from the the device 
        without changing the register. Does NOT perform LE/BE conversion
        '''
        return self._pig.i2c_read_device(self._handle,num_bytes)

    def write_device(self,data):
        '''
        Write bytes to the device without specifying register.
        Does NOT perform LE/BE conversion
        '''
        self._pig.i2c_write_device(self._handle,data)

    def read_word(self):
        '''
        Read two words directly from the the device 
        without changing the register. 
        '''
        return self._be16_to_le(self._pig.i2c_read_word(self._handle))

    def write_word(self,word):
        '''
        Write two bytes to the device without specifying register.
        '''
        self._pig.i2c_write_word(self._handle,self._le16_to_be(word))

    def read_register(self,register):
        '''
        Read 2 bytes from the specified register(denoted by a single byte)
        '''
        return self._be16_to_le(self._pig.i2c_read_word_data(self._handle,register))

    def write_register(self,register,word):
        '''
        Write 2 bytes to the specified register (denoted by a single byte)
        '''
        self._pig.i2c_write_word_data(self._handle,register,self._le16_to_be(word))

    def _be16_to_le(self,word):
        '''BigEndian to LittleEndian conversion for signed 2 Byte integers (2 complement).'''
        if(word < 0):
            word = 2**16 + word
        return self._byteswap(word)

    def _le16_to_be(self,word):
        '''Little Endian to BigEndian conversion for unsigned 2Byte integers (2 complement).'''
        word = self._byteswap(word)
        #if(word >= 2**15):
        #    word = word-2**16
        return word

    def _byteswap(self,word):
        '''Revert Byte order for Words (2 Bytes, 16 Bit).'''
        word = (word>>8 |word<<8)&0xFFFF
        return word

    class Register:
        '''
        Describes a writable configuration register. Has Dynamically-defined
        attributes corresponding to the fields described by the passed arguments.
        Takes as arguments two tuples of equal length, the first of which
        names each field and the second being a tuple of tuples containing
        the (human readable) possible settings/values for each field.  
        '''
        def __init__(self,fields,values):
            self._fields = fields
            
            ''' Dynamically initialize attributes'''
            offset = 0
            for f,v in zip(reversed(fields),reversed(values)):
                setattr( self, f, self.ConfigField(offset, len(v)-1, OrderedDict(zip( v, range(len(v)) )) ) )
                offset += (len(v)-1).bit_length()
                
        def unpack(self,cfg):
            '''
            Given the contents of a register in integer form, returns a dict of fields and their current settings
            '''
            return OrderedDict(zip(self._fields, ( getattr(getattr(self,field), 'unpack' )(cfg) for field in self._fields )))
        
        def pack(self,cfg,**kwargs):
            '''
            Given an initial integer representation of a register and an
            arbitrary number of field=value settings, returns an integer
            representation of the register incorporating the new settings
            '''
            for field,value in kwargs.items():
                if hasattr(self,field) and value is not None:
                    cfg = getattr( getattr(self,field), 'insert' )(cfg,value)
            return cfg

        class ConfigField:
            '''
            Describes a configurable field in a writable register.
            '''
            def __init__(self,offset,mask,values):
                self._OFFSET    = offset
                self._MASK      = mask
                self._VALUES    = values
                
            def offset(self):
                return self._OFFSET

            def info(self):
                ''' Returns a list containing stuff '''
                return [ self._OFFSET, self._MASK, self._VALUES ]
            
            def unpack(self,cfg):
                ''' Extracts setting from passed 16-bit config & returns human readable result '''
                return OrderedDict(map(reversed,self._VALUES.items()))[ self.extract(cfg) ]
            
            def pack(self,value):
                '''Takes a human-readable setting and returns a bit-shifted integer'''
                return self._VALUES[value] << self._OFFSET
                
            def insert(self,cfg,value):
                ''' 
                Performs validation and then does a bitwise replacement on passed config with
                the passed value. Returns integer representation of the new config.
                '''
                if value not in self._VALUES.keys():
                    raise ValueError("ConfigField must be one of: {}".format(self._VALUES.keys()))
                return ( cfg & ~(self._MASK<<self._OFFSET) )|( self._VALUES[value] << self._OFFSET )
                
            def extract(self,cfg):
                '''Extracts setting from passed 16-bit config & returns integer representation'''
                return ( cfg & (self._MASK<<self._OFFSET) )>>self._OFFSET

class spiDevice(Device):
    '''
    A class wrapper for pigpio SPI handles. Not implemented.
    '''
    def __init(self,pig,spi_channel,baudrate):
        super().__init__(pig)
        self._handle = self._pig.spi_open(spi_channel,baudrate)
        	
class ads1115(i2cDevice):  
    '''
    Class for the ADS1115 16 bit, 4 Channel Analog to Digital Converter.
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
        
class Sensor(abc.ABC):
    '''
    Class describing generalized sensors
    '''
    def __init__(self):
        _DATA   = np.zeros(128)
        _N      = 0
    @property
    def data(self,n=None):
        if n is None: return _DATA
        else: return _DATA[n]
        
    @property 
    def n(self):
        return self._N
        
    @abc.abstractmethod
    def read(self):
        self._N +=1
    
    def reset(self):
        self._DATA  = np.zeros(128)
        self._N     = 0

    
class SFM3200(Sensor,i2cDevice):
    '''
    Datasheet:
        https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    '''
    _DEFAULT_ADDRESS     = 0x40 # SFM3x00 Flow sensor address
    _FLOW_OFFSET         = 32768
    _FLOW_SCALE_FACTOR   = 120

    def __init__(self,pig,address=_DEFAULT_ADDRESS):
        i2cDevice.__init__(pig,address)
        Sensor.__init__()
        self.reset()
        self._start()

    def read(self):
        return self._convert(self._raw_read())

    def _raw_read(self,pig):
        '''
        Performs a read on the sensor, converts recieved bytearray, 
        discards the last two bytes (crc values - could implement in future),
        and returns a signed int converted from the big endian two 
        complement that remains.
        '''
        return int.from_bytes(self.read_device(4)[2],'big',signed=True)

    def reset(self):
        super.reset()
        self.write_word(0x2000)  # soft reset
        time.sleep(.08)                     # 80 ms soft reset time 

    def _start(self):
        self.write_word(0x1000)  # start measurement
        time.sleep(.1)                     # start-up time is 100 ms.

    def _convert(self,value):
        # Convert raw int to a flow reading represaented by a floating-point
        # number with units slm.
        # Source: https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        return (value-self._FLOW_OFFSET)/self._FLOW_SCALE_FACTOR
	
class AnalogSensor(Sensor):
    '''
    General class describing an anlog sensor attached to an ADC.
    If instantiated without a subclass, represents a voltmeter with range 0-1.0.
    '''

    def __init__(   self, adc, channel,
                    calibration=(0,5,),
                    gain=None, data_rate=None, mode=None ):
        if type(calibration) != tuple:
                raise TypeError('arg calibration must be a tuple of the form (low,high)')
        super().__init__()
        self.channel    = channel
        self.gain       = adc.gain if gain is None else gain
        self.data_rate  = adc.data_rate if data_rate is None else data_rate
        self.mode       = adc.mode if mode is None else mode
        
    def read(self):
        '''
        Returns a value in the range of 0 - 1 corresponding to a fraction
        of the full input range of the sensor
        '''
        return self._convert(self._raw_read())
    def calibrate(self,calibration=None):
        if calibration is not None:
            if type(calibration) != tuple:
                raise TypeError('arg calibration must be a tuple of the form (low,high)')
            elif calibration is not None: 
                self.calibration = calibration
            else:
                for i in range(50):
                    self.read()
                    print('Analog Sensor Calibration @ %6.4f V'%(self._DATA[self._N]),end='\r')
                    time.sleep(.1)
                self.calibration[0] = np.mean(self.data(50))
                print('Calibrated low-end of Analog sensor  @ %6.4f V'%(self.calibration[0]))

    def _raw_read(self):
        '''
        Returns raw voltage
        '''
        return self.adc.get_voltage(self.channel,self.gain,self.data_rate,self.mode)

    def _convert(self,raw):
        '''
        Scales raw voltage into the range 0 - 1 
        '''
        return raw - calibration[0]/(calibration[1]-calibration[0])
            
class P4vMini(Sensor):
    '''
        Analog gauge pressure sensor with range of 0 - 20" h20.
        Datasheet calibration low is 0.25V and high is 4.0V
    '''
    _default_offset_voltage = 0.25
    _default_output_span    = 4
    ''' Maximum reading in cm h20: 2.54 cm/in * 20" h20 * 1.0 normalized output '''
    _conversion_factor      = 2.54*20 

    def __init__(   self, adc, channel,
                    calibration=(0.25,4.0),
                    gain=1, data_rate=860, mode=None ):
        super().__init(self, adc, channel, calibration, gain, data_rate, mode)

    def _convert(self,raw):
        return self._conversion_factor*self.read()

# ~ class Pin

# ~ class InputPin

# ~ class OutputPin

# ~ class PWMOutput

# ~ class Valve(abc.ABC):
	
# ~ class SolenoidValve(Valve,OutputPin):
	
# ~ class ProportionalValve(Valve,PWMOuput): # or DAC out if it comes to that

# ~ class OxygenSensor(AnalogSensor):
	
# ~ class HumiditySensor(Sensor):
	
# ~ class TemperatureSensor(Sensor):
