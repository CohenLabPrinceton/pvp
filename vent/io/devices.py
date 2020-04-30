'''
Subclass implementations of specific sensor devices.
'''
from .iobase import Sensor, AnalogSensor, i2cDevice, spiDevice, OutputPin, PWMOutput
from time import sleep
import struct


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
    The Conversion Register is read-only and contains a 16bit
    representation of the requested value (provided the conversion is
    ready).

    The Lo-thresh & Hi-thresh Registers are not Utilized here. However,
    their function and usage are described in the datasheet. Should you
    want to extend the functionality implemented here.
    '''

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        super().__init__(address,i2c_bus,pig)
        ''' Initializes registers: Pointer register is write only,
        config is R/W. Sets initial value of _last_cfg to what is
        actually on the ADS.Packs default settings into _cfg, but does
        not actually write to ADC - that occurs when read_conversion()
        is called.
        '''
        self.pointer    = self.Register(self._POINTER_FIELDS,self._POINTER_VALUES)
        self._config    = self.Register(self._CONFIG_FIELDS,self._CONFIG_VALUES)
        self._last_cfg  = self._read_last_cfg()
        self._cfg       = self._config.pack(cfg  = self._last_cfg,
                                            MUX  = self._DEFAULT_VALUES['MUX'],
                                            PGA  = self._DEFAULT_VALUES['PGA'],
                                            MODE = self._DEFAULT_VALUES['MODE'],
                                            DR   = self._DEFAULT_VALUES['DR'] )

    def read_conversion(self,channel=None,gain=None,mode=None,data_rate=None):
        ''' Returns a voltage (expressed as a float) corresponding to a
        channel on the ADC. The channel to read from, along with the
        gain, mode, and sample rate of the conversion may be may be
        specified as optional parameters. If read_conversion() is called
        with no parameters, the resulting voltage corresponds to the
        channel last read from and the same conversion settings.
        '''
        return self._read_conversion(  channel=channel,
                            gain=gain,
                            mode=mode,
                            data_rate=data_rate) * self._config.PGA.unpack(self._cfg) / 32767

    def print_config(self):
        ''' Returns the human-readable configuration for the next read.
        '''
        return self._config.unpack(self._cfg)

    @property
    def config(self):
        ''' Returns the Register object of the config register.
        '''
        return self._config

    @property
    def cfg(self):
        ''' Returns the contents (as a 16-bit unsigned integer) of the
        configuration that will be written to the config register when
        read_conversion() is next called.
        '''
        return self._cfg

    def _read_conversion(self,channel=None,gain=None,mode=None,data_rate=None):
        ''' Backend for read_conversion(). Returns the contents of the
        16-bit conversion register as an unsigned integer.

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
                tick = self.pig.get_current_tick()
                while ((self.pig.get_current_tick() - tick) < 1000000/data_rate):
                    pass
        return self.read_register(self.pointer.P.pack('CONVERSION'))

    def _read_last_cfg(self):
        ''' Reads the config register and returns the contents as a
        16-bit unsigned integer; updates internal record _last_cfg.
        '''
        self._last_cfg = self.read_register(self.pointer.P.pack('CONFIG'))
        return self._last_cfg

    def _ready(self):
        ''' Return status of ADC conversion.
        OS = 0: Device is currently performing a conversion
        OS = 1: Device is not currently performing a conversion
        '''
        return self.read_register(self.pointer.P.pack('CONFIG')) >> 15

class P4vMini(AnalogSensor):
    ''' Analog gauge pressure sensor with range of 0 - 20" h20. The
    calibration outlined in the datasheet has low =  0.25V and
    high = 4.0V (give or take a bit). The conversion factor is derived
    from the sensor's maximum output of 20 in(h20), and we want sensor
    readings in cm h20: (2.54 cm/in * 20" h20) * read() = observed cmh20

    The only difference between this device and a generic AnalogSensor
    is its calibration, and the additional unit conversion in _convert()
    '''
    _DEFAULT_OFFSET_VOLTAGE = 0.25
    _DEFAULT_OUTPUT_SPAN    = 4
    _CONVERSION_FACTOR      = 2.54*20

    def __init__(   self,
                    adc,
                    channel,
                    offset_voltage  = _DEFAULT_OFFSET_VOLTAGE,
                    output_span     = _DEFAULT_OUTPUT_SPAN,
                    gain            = 4.096,
                    data_rate       = 860,
                    mode            = None
                    ):
        super().__init__(   adc,
                            channel,
                            offset_voltage,
                            output_span,
                            gain,
                            data_rate,
                            mode
                            )
        # A check here to make sure calibrated offset voltage is
        #  reasonably close to what is currently coming from the sensor
        #   would be prudent. A warning is probably sufficient.

    def _convert(self,raw):
        ''' Overloaded to map AnalogSensor's normalized output into the
        desired units of cm(h20)'''
        return self._CONVERSION_FACTOR*super()._convert(raw)


class OxygenSensor(AnalogSensor):
    ''' Not yet implemented. Would need to define calibration and
    overload _convert() to add unit conversion.
    '''  
#    def __init__(self):
#        raise NotImplementedError


class SFM3200(Sensor,i2cDevice):
    ''' Datasheet:
         https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    '''
    _DEFAULT_ADDRESS     = 0x40
    _FLOW_OFFSET         = 32768
    _FLOW_SCALE_FACTOR   = 120

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        i2cDevice.__init__(self,address,i2c_bus,pig)
        Sensor.__init__(self)
        self.reset()
        self._start()

    def reset(self):
        ''' Extended to add device specific behavior: Asks the sensor
        to perform a soft reset. 80 ms soft reset time.
        '''
        super().reset()
        self.write_word(0x2000)
        sleep(.08)

    def _start(self):
        ''' Device specific:Sends the 'start measurement' command to the
        sensor. Start-up time once command has been recieved is
        'less than 100ms'
        '''
        self.write_word(0x1000)
        sleep(.1)

    def _verify(self,value):
        ''' No further verification needed for this sensor. Onboard
        chip handles all that. Could throw in a CRC8 checker instead of
        discarding them in _convert().
        '''
        return True

    def _convert(self,raw):
        ''' Overloaded to replace with device-specific protocol.
        Convert raw int to a flow reading having type float with
        units slm. Implementation differs from parent for clarity and
        consistency with source material.

        Source:
          https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        '''
        return (struct.unpack('>H',value[:2])[0] - self._FLOW_OFFSET) / self._FLOW_SCALE_FACTOR

    def _raw_read(self):
        ''' Performs an read on the sensor, converts recieved bytearray,
        discards the last two bytes (crc values - could implement in future),
        and returns a signed int converted from the big endian two
        complement that remains.
        '''
        return self.read_device(4)


class HumiditySensor(Sensor):
    ''' Not yet implemented.
    '''
    #def __init__(self):
    #    raise NotImplementedError


class TemperatureSensor(spiDevice):
    ''' Not yet implemented
    '''
    #def __init__(self):
    #    raise NotImplementedError


class SolenoidValve(OutputPin):
    ''' An extension of OutputPin which uses valve terminology for its 
    methods. Also allows configuring both normally open and normally
    closed valves (called the "form" of the valve).
    '''
    _FORMS = {  'Normally Closed'   : 0,
                'Normally Open'     : 1 }
    def __init__( self, pin, form='Normally Closed', pig=None ):
        self.form = self._FORMS[form]
        super().__init__(pin,pig)

    @property
    def form(self):
        ''' Returns the human-readable form of the valve
        '''
        return dict(map(reversed,self._FORMS.items()))[self._form]

    @form.setter
    def form(self,f):
        ''' Performs validation on requested form and then sets it.
        '''
        if f not in self._FORMS:
            raise ValueError('form must be either NC for Normally Closed or NO for Normally Open')
        else: self._form = self._FORMS[f]

    def open(self):
        ''' Energizes valve if Normally Closed. De-energizes if
        Normally Open
         '''
        if self._form: self.off()
        else: self.on()

    def close(self):
        ''' De-energizes valve if Normally Closed. Energizes if
        Normally Open'''
        if not self._form: self.off()
        else: self.on()


class PWMControlValve(PWMOutput):
    ''' An extension of PWMOutput which incorporates linear 
    compensation of the valve's response. 
    '''
    # or DAC out if it comes to that
    def __init__(self,pin,form='Normally Closed',initial_duty=0,frequency=None,pig=None):
        super().__init__(pin,initial_duty,frequency,pig)
        
        # TODO: sort out API commonality w solenoid valve.
        
        def get(self):
            '''Overloaded to return the linearized setpoint corresponding
            to the current duty cycle according to the valve's response curve'''
            return self.inverse_response(self.duty)

        def set(self,setpoint):
            '''Overloaded to determine & set the duty cycle corresponting
            to the requested linearized setpoint according to the valve's
            response curve'''
            self.duty = self.response(setpoint)

        def response(self,setpoint):
            '''Setpoint takes a value in the range (0,100) so as not to
            confuse with duty cycle, which takes a value in the range (0,1).
            Response curves are specific to individual valves and are to
            be implemented by subclasses. If not implemented in subclass,
            defaults to a perfectly linear response and tosses a warning'''
            raise RuntimeWarning('Control Valve response function not implemented by subclass')
            return setpoint/100

        def inverse_response(self,duty_cycle):
            '''Inverse of response. Given a duty cycle in the range (0,1),
            returns the corresponding linear setpoint in the range (0,100).
            Tosses a warning if not implemented by subclass.'''
            raise RuntimeWarning('Control Valve inverse_respone function not implemented by subclass')
