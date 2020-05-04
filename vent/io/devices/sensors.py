import time
from abc import ABC, abstractmethod
from time import sleep

import numpy as np

from vent.io import be16_to_native
from vent.io.devices import I2CDevice


class Sensor(ABC):
    """ Abstract base Class describing generalized sensors. Defines a
    mechanism for limited internal storage of recent observations and
    methods to pull that data out for external use.
    """
    _DEFAULT_STORED_OBSERVATIONS = 128

    def __init__(self):
        """ Upon creation, calls update() to ensure that if get is
        called there will be something to return
        """
        self._data = np.zeros(
            self._DEFAULT_STORED_OBSERVATIONS,
            dtype=np.float16
        )
        self._i = 0
        self._data_length = self._DEFAULT_STORED_OBSERVATIONS
        self._last_timestamp = -1

    def update(self):
        """ Make a sensor reading, verify that it makes sense and store
        the result internally. Returns True if reading was verified and
        False if something went wrong.
        """
        value = self._read()
        if self._verify(value):
            self.__store_last(value)
            self._last_timestamp = time.time()
        return self._verify(value)

    def get(self):
        """ Return the most recent sensor reading.
        """
        if self._last_timestamp == -1:
            raise RuntimeWarning('get() called before update()')
        return self._data[(self._i - 1) % self._data_length]

    def age(self):
        """ Returns the time since the last sensor update, in seconds.
        """
        if self._last_timestamp == -1:
            raise RuntimeError('age() called before update()')
        return time.time() - self._last_timestamp

    def reset(self):
        """ Resets the sensors internal memory. May be overloaded by
        subclasses to extend functionality specific to a device.
        """
        self._data = np.zeros(self.data_length, dtype=np.float16)
        self._i = 0

    @property
    def data(self):
        """ Generalized, not necessarily performant. Returns an ndarray
        of observations arranged oldest to newest. Result has length
        equal to the lessor of self.n and the number of observations
        made.

        Note: ndarray.astype(bool) returns an equivalent sized array
        with True for each nonzero element and False everywhere else.
        """
        rolled = np.roll(self._data, self.data_length - self._i)
        return rolled[rolled.astype(bool)]

    @property
    def data_length(self):
        """ Returns the number of observations kept in the Sensor's
        internal ndarray. Once the ndarray has been filled, the sensor
        begins overwriting the oldest elements of the ndarray with new
        observations such that the size of the internal storage stays
        constant.
        """
        return self._data_length

    @data_length.setter
    def data_length(self, new_data_length):
        """ Set a new length for stored observations. Clears existing
        observations and resets. """
        self._data_length = new_data_length
        self.reset()

    def _read(self):
        """ Calls _raw_read and scales the result before returning it
        """
        return self._convert(self._raw_read())

    @abstractmethod
    def _verify(self, value):
        """ Validate reading and throw exception/alarm if sensor does not
        appear to be working correctly
        """
        raise NotImplementedError('Subclass must implement _verify()')

    @abstractmethod
    def _convert(self, raw):
        """ Converts a raw reading from a sensor in whatever forma
        the device communicates with into a meaningful result.
        """
        raise NotImplementedError('Subclass must implement _raw_read()')

    @abstractmethod
    def _raw_read(self):
        """ Requests a new observation from the device and returns the
        raw result in whatever format/units the device communicates with
        """
        raise NotImplementedError('Subclass must implement _raw_read()')

    def __store_last(self, value):
        """ Takes a value and stores it in self.data. Increments counter
        """
        self._data[self._i] = value
        self._i = (self._i + 1) % self.data_length


class AnalogSensor(Sensor):
    """ Generalized class describing an analog sensor attached to the
    ADS1115 analog to digital converter. Inherits from the sensor base
    class and extends with functionality specific to analog sensors
    attached to the ads1115.

    If instantiated without a subclass, conceptually represents a
    voltmeter with a normalized output.
    """
    _DEFAULT_offset_voltage = 0
    _DEFAULT_output_span = 5
    _CONVERSION_FACTOR = 1
    _DEFAULT_CALIBRATION = {
        'offset_voltage': _DEFAULT_offset_voltage,
        'output_span': _DEFAULT_output_span
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
            self.offset_voltage = np.mean(self.data[-50:])
            # PRINT FOR DEBUG / HARDWARE TESTING
            print("Calibrated low-end of AnalogSensor @",
                  ' %6.4f V' % self.offset_voltage)

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
                (raw - getattr(self, 'offset_voltage'))
                / (getattr(self, 'output_span') + getattr(self, 'offset_voltage'))
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
        user configurable or calibration that have not been write (i.e.
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
        as user configurable or calibration fields. If so, write the value
        as an attribute like: self.KEY = VALUE. Keeps track of how many
        attributes are write in this way; if at the end there unknown
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
        'offset_voltage': 0.25,
        'output_span': 4.0
    }
    _CONVERSION_FACTOR = 2.54 * 20

    def __init__(self, adc, mux, **calibration_kwargs):
        super().__init__(adc, MUX=mux, **calibration_kwargs)

        # A check here to make sure calibrated offset voltage is
        #  reasonably close to what is currently coming from the sensor
        #   would be prudent. A warning is probably sufficient.

    def _verify(self, value):
        """ Extends superclass value to function with a conversion
        factor
        """
        return super()._verify(value / self._CONVERSION_FACTOR)

    def _convert(self, raw):
        """ Overloaded to map AnalogSensor's normalized output into the
        desired units of cm(h20)"""
        return self._CONVERSION_FACTOR * super()._convert(raw)


class SFM3200(Sensor, I2CDevice):
    """ Datasheet:
         https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    """
    _DEFAULT_ADDRESS = 0x40
    _FLOW_OFFSET = 32768
    _FLOW_SCALE_FACTOR = 120

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        I2CDevice.__init__(self, address, i2c_bus, pig)
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

    def _verify(self, value):
        """ No further verification needed for this sensor. Onboard
        chip handles all that. Could throw in a CRC8 checker instead of
        discarding them in _convert().
        """
        return True

    def _convert(self, raw):
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