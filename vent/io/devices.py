"""
Subclass implementations of specific sensor devices.
"""
import numpy as np
from .iobase import Sensor, I2CDevice, OutputPin, PWMOutput, be16_to_native
from time import sleep


class ADS1115(I2CDevice):
    """ Description:
    Class for the ADS1115 16 bit, 4 Channel ADC.
    Datasheet:
     http://www.ti.com/lit/ds/symlink/ads1114.pdf?ts=1587872241912

    Default Values:
     Default configuration for vent:     0xC3E3
     Default configuration on power-up:  0x8583
    """
    _DEFAULT_ADDRESS = 0x48
    _DEFAULT_VALUES  = {'MUX':0, 'PGA':4.096, 'MODE':'SINGLE', 'DR':860}

    """ Address Pointer Register (write-only) """
    _POINTER_FIELDS = ('P')
    _POINTER_VALUES = (
            (
                'CONVERSION',
                'CONFIG',
                'LO_THRESH',
                'HIGH_THRESH'
            ),
    )

    """ Config Register (R/W) """
    _CONFIG_FIELDS = (
            'OS',
            'MUX',
            'PGA',
            'MODE',
            'DR',
            'COMP_MODE',
            'COMP_POL',
            'COMP_LAT',
            'COMP_QUE'
    )
    _CONFIG_VALUES  = (
            ('NO_EFFECT', 'START_CONVERSION'),
            ((0, 1), (0, 3), (1, 3), (2, 3), 0, 1, 2, 3),
            (6.144, 4.096, 2.048, 1.024, 0.512, 0.256, 0.256, 0.256),
            ('CONTINUOUS', 'SINGLE'),
            (8, 16, 32, 64, 128, 250, 475, 860 ),
            ('TRADIONAL', 'WINDOW'),
            ('ACTIVE_LOW', 'ACTIVE_HIGH'),
            ('NONLATCHING', 'LATCHING'),
            (1, 2, 3, 'DISABLE')
    )
    USER_CONFIGURABLE_FIELDS   = ('MUX', 'PGA', 'MODE', 'DR')
    """ Note:
    The Conversion Register is read-only and contains a 16bit
    representation of the requested value (provided the conversion is
    ready).

    The Lo-thresh & Hi-thresh Registers are not Utilized here. However,
    their function and usage are described in the datasheet. Should you
    want to extend the functionality implemented here.
    """

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        """ Initializes registers: Pointer register is write only,
        config is R/W. Sets initial value of _last_cfg to what is
        actually on the ADS.Packs default settings into _cfg, but does
        not actually write to ADC - that occurs when read_conversion()
        is called.
        """
        super().__init__(address,i2c_bus,pig)
        self.pointer    = self.Register(self._POINTER_FIELDS,self._POINTER_VALUES)
        self._config    = self.Register(self._CONFIG_FIELDS,self._CONFIG_VALUES)
        self._last_cfg  = self._read_last_cfg()
        self._cfg       = self._config.pack(cfg  = self._last_cfg, **self._DEFAULT_VALUES)

    def read_conversion(self,**kwargs):
        """ Returns a voltage (expressed as a float) corresponding to a
        channel on the ADC. The channel to read from, along with the
        gain, mode, and sample rate of the conversion may be may be
        specified as optional parameters. If read_conversion() is called
        with no parameters, the resulting voltage corresponds to the
        channel last read from and the same conversion settings.
        """
        return (
            self._read_conversion(**kwargs)
            * self._config.PGA.unpack(self.cfg) / 32767
        )

    def print_config(self):
        """ Returns the human-readable configuration for the next read.
        """
        return self._config.unpack(self.cfg)

    @property
    def config(self):
        """ Returns the Register object of the config register.
        """
        return self._config

    @property
    def cfg(self):
        """ Returns the contents (as a 16-bit unsigned integer) of the
        configuration that will be written to the config register when
        read_conversion() is next called.
        """
        return self._cfg

    def _read_conversion(self,**kwargs):
        """ Backend for read_conversion(). Returns the contents of the
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
        """
        self._cfg = self._config.pack(cfg=self.cfg,**kwargs)
        mode = self.print_config()['MODE']
        if self._cfg != self._last_cfg or mode == 'SINGLE':
            self.write_register(self.pointer.P.pack('CONFIG'), self.cfg)
            self._last_cfg  = self.cfg
            data_rate = self._config.DR.unpack(self.cfg)
            while not ( self._ready() or  mode == 'CONTINUOUS' ):
                tick = self.pig.get_current_tick()
                while ((self.pig.get_current_tick() - tick) < 1000000/data_rate):
                    pass
        return self.read_register(self.pointer.P.pack('CONVERSION'),signed=True)

    def _read_last_cfg(self):
        """ Reads the config register and returns the contents as a
        16-bit unsigned integer; updates internal record _last_cfg.
        """
        self._last_cfg = self.read_register(self.pointer.P.pack('CONFIG'))
        return self._last_cfg

    def _ready(self):
        """ Return status of ADC conversion.
        OS = 0: Device is currently performing a conversion
        OS = 1: Device is not currently performing a conversion
        """
        return self.read_register(self.pointer.P.pack('CONFIG')) >> 15


class AnalogSensor(Sensor):
    """ Generalized class describing an analog sensor attached to the
    ADS1115 analog to digital converter. Inherits from the sensor base
    class and extends with functionality specific to analog sensors
    attached to the ads1115.

    If instantiated without a subclass, conceptually represents a
    voltmeter with a normalized output.
    """
    _DEFAULT_OFFSET_VOLTAGE = 0
    _DEFAULT_OUTPUT_SPAN = 5
    _CONVERSION_FACTOR = 1
    _DEFAULT_CALIBRATION = {
        'OFFSET_VOLTAGE': _DEFAULT_OFFSET_VOLTAGE,
        'OUTPUT_SPAN': _DEFAULT_OUTPUT_SPAN
    }

    def __init__(self, adc, **kwargs):
        """ Links analog sensor on the ADC with configuration options
        specified. If no options are specified, it assumes the settings
        currently on the ADC.
        """
        super().__init__()
        self.adc = adc
        if 'MUX' not in (kwargs.keys()):
            raise TypeError(
                'User must specify MUX for AnalogSensor creation'
            )
        self._check_and_set_attr(**kwargs)

    def calibrate(self, **kwargs):
        """ Sets the calibration of the sensor, either to the values
        contained in the passed tuple or by some routine; the current
        routine is pretty rudimentary and only calibrates offset voltage
        """
        if kwargs:
            for fld, val in kwargs.items():
                if fld in self._DEFAULT_CALIBRATION.keys():
                    setattr(self, fld, val)
        else:
            for _ in range(50):
                self.update()
                # PRINT FOR DEBUG / HARDWARE TESTING
                print(
                    "Analog Sensor Calibration @ {:6.4f}".format(self.data[self.data.shape[0] - 1]),
                    end='\r'
                )
                sleep(.1)
            self.OFFSET_VOLTAGE = np.mean(self.data[-50:])
            # PRINT FOR DEBUG / HARDWARE TESTING
            print("Calibrated low-end of AnalogSensor @",
                  ' %6.4f V' % self.OFFSET_VOLTAGE)

    def _read(self):
        """ Returns a value in the range of 0 - 1 corresponding to a
        fraction of the full input range of the sensor
        """
        return self._convert(self._raw_read())

    def _verify(self, value):
        """ Checks to make sure sensor reading was indeed in [0, 1]
        """
        report = bool(0 <= value <= 1)
        if not report:
            print(value)
        return report

    def _convert(self, raw):
        """ Scales raw voltage into the range 0 - 1
        """
        return (
                (raw - getattr(self, 'OFFSET_VOLTAGE'))
                / (getattr(self, 'OUTPUT_SPAN') + getattr(self, 'OFFSET_VOLTAGE'))
        )

    def _raw_read(self):
        """ Builds kwargs from configured fields to pass along to adc,
        then calls adc.read_conversion(), which returns a raw voltage.
        """
        fields = self.adc.USER_CONFIGURABLE_FIELDS
        kwargs = dict(zip(
            fields,
            (getattr(self, field) for field in fields)
        ))
        return self.adc.read_conversion(**kwargs)

    def _fill_attr(self):
        """ Examines self to see if there are any fields identified as
        user configurable or calibration that have not been set (i.e.
        were not passed to __init__ as **kwargs). If a field is missing,
        grabs the default value either from the ADC or from
        _DEFAULT_CALIBRATION and sets it as an attribute.
        """
        for cfld in self.adc.USER_CONFIGURABLE_FIELDS:
            if not hasattr(self, cfld):
                setattr(
                    self,
                    cfld,
                    getattr(self.adc.config, cfld).unpack(self.adc.cfg)
                )
        for dcal, value in self._DEFAULT_CALIBRATION.items():
            if not hasattr(self, dcal):
                setattr(self, dcal, value)

    def _check_and_set_attr(self, **kwargs):
        """ Checks to see if arguments passed to __init__ are recognized
        as user configurable or calibration fields. If so, set the value
        as an attribute like: self.KEY = VALUE. Keeps track of how many
        attributes are set in this way; if at the end there unknown
        arguments leftover, raises a TypeError; otherwise, calls
        _fill_attr() to fill in fields that were not passed
        """
        allowed = (
            *self.adc.USER_CONFIGURABLE_FIELDS,
            *self._DEFAULT_CALIBRATION.keys(),
        )
        result = 0
        for fld, val in kwargs.items():
            if fld in allowed:
                setattr(self, fld, val)
                result += 1
        if result != len(kwargs):
            raise TypeError('AnalogSensor was passed unknown field(s)')
        self._fill_attr()


class P4vMini(AnalogSensor):
    """ Analog gauge pressure sensor with range of 0 - 20" h20. The
    calibration outlined in the datasheet has low =  0.25V and
    high = 4.0V (give or take a bit). The conversion factor is derived
    from the sensor's maximum output of 20 in(h20), and we want sensor
    readings in cm h20: (2.54 cm/in * 20" h20) * read() = observed cmh20

    The only difference between this device and a generic AnalogSensor
    is its calibration, and the additional unit conversion in _convert()
    """
    _CALIBRATION = {
        'OFFSET_VOLTAGE' : 0.25,
        'OUTPUT_SPAN'    : 4.0
    }
    _CONVERSION_FACTOR      = 2.54*20

    def __init__(self, adc, MUX, **_CALIBRATION):
        super().__init__(adc, MUX=MUX)

        # A check here to make sure calibrated offset voltage is
        #  reasonably close to what is currently coming from the sensor
        #   would be prudent. A warning is probably sufficient.

    def _verify(self, value):
        """ Extends superclass value to function with a conversion
        factor
        """
        return super()._verify(value/self._CONVERSION_FACTOR)

    def _convert(self, raw):
        """ Overloaded to map AnalogSensor's normalized output into the
        desired units of cm(h20)"""
        return self._CONVERSION_FACTOR*super()._convert(raw)


#class OxygenSensor(AnalogSensor):
#    """ Not yet implemented. Would need to define calibration and
#    overload _convert() to add unit conversion.
#    """
#    def __init__(self):
#        raise NotImplementedError


class SFM3200(Sensor,I2CDevice):
    """ Datasheet:
         https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    """
    _DEFAULT_ADDRESS     = 0x40
    _FLOW_OFFSET         = 32768
    _FLOW_SCALE_FACTOR   = 120

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        I2CDevice.__init__(self,address,i2c_bus,pig)
        Sensor.__init__(self)
        self.reset()
        self._start()

    def reset(self):
        """ Extended to add device specific behavior: Asks the sensor
        to perform a soft reset. 80 ms soft reset time.
        """
        super().reset()
        self.write_device(0x2000)
        sleep(.08)

    def _start(self):
        """ Device specific:Sends the 'start measurement' command to the
        sensor. Start-up time once command has been recieved is
        'less than 100ms'
        """
        self.write_device(0x1000)
        sleep(.1)

    def _verify(self,value):
        """ No further verification needed for this sensor. Onboard
        chip handles all that. Could throw in a CRC8 checker instead of
        discarding them in _convert().
        """
        return True

    def _convert(self,raw):
        """ Overloaded to replace with device-specific protocol.
        Convert raw int to a flow reading having type float with
        units slm. Implementation differs from parent for clarity and
        consistency with source material.

        Source:
          https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        """
        return (raw - self._FLOW_OFFSET) / self._FLOW_SCALE_FACTOR

    def _raw_read(self):
        """ Performs an read on the sensor, converts recieved bytearray,
        discards the last two bytes (crc values - could implement in future),
        and returns a signed int converted from the big endian two
        complement that remains.
        """
        return be16_to_native(self.read_device(4))


#class HumiditySensor(Sensor):
#    """ Not yet implemented.
#    """
#    def __init__(self):
#        raise NotImplementedError


#class TemperatureSensor(Sensor, SPIDevice):
#    """ Not yet implemented
#    """
#    def __init__(self):
#        raise NotImplementedError


class SolenoidValve(OutputPin):
    """ An extension of OutputPin which uses valve terminology for its
    methods. Also allows configuring both normally open and normally
    closed valves (called the "form" of the valve).
    """
    _FORMS = {  'Normally Closed'   : 0,
                'Normally Open'     : 1 }
    def __init__( self, pin, form='Normally Closed', pig=None ):
        self.form = form
        super().__init__(pin,pig)

    @property
    def form(self):
        """ Returns the human-readable form of the valve
        """
        return dict(map(reversed,self._FORMS.items()))[self._form]

    @form.setter
    def form(self,f):
        """ Performs validation on requested form and then sets it.
        """
        if f not in self._FORMS.keys():
            raise ValueError('form must be either NC for Normally Closed or NO for Normally Open')
        else:
            self._form = self._FORMS[f]

    def open(self):
        """ Energizes valve if Normally Closed. De-energizes if
        Normally Open
         """
        if self._form:
            self.off()
        else:
            self.on()

    def close(self):
        """ De-energizes valve if Normally Closed. Energizes if
        Normally Open"""
        if self.form == 'Normally Closed':
            self.off()
        else:
            self.on()


class PWMControlValve(PWMOutput):
    """ An extension of PWMOutput which incorporates linear
    compensation of the valve's response.
    """
    # .close() is not working for this dude! 
    def __init__(self,pin,form='Normally Closed',initial_duty=0,frequency=None,pig=None):
        super().__init__(pin,initial_duty,frequency,pig)

        # TODO: sort out API commonality w solenoid valve.

        def get(self):
            """Overridden to return the linearized setpoint corresponding
            to the current duty cycle according to the valve's response curve"""
            return self.inverse_response(self.duty)

        def set(self,setpoint):
            """Overridden to determine & set the duty cycle corresponting
            to the requested linearized setpoint according to the valve's
            response curve"""
            self.duty = self.response(setpoint)

        def response(self,setpoint):
            """Setpoint takes a value in the range (0,100) so as not to
            confuse with duty cycle, which takes a value in the range (0,1).
            Response curves are specific to individual valves and are to
            be implemented by subclasses. If not implemented in subclass,
            defaults to a perfectly linear response"""
            return setpoint/100

        def inverse_response(self,duty_cycle):
            """Inverse of response. Given a duty cycle in the range (0,1),
            returns the corresponding linear setpoint in the range (0,100).
            """
            return duty_cycle*100
