from vent.io import IODeviceBase


class Pin(IODeviceBase):
    """
    Base Class wrapping pigpio methods for interacting with GPIO pins on
    the raspberry pi. Subclasses include InputPin, OutputPin; along with
    any specialized pins or specific devices defined in vent.io.actuators
    & vent.io.sensors (note: actuators and sensors do not need to be tied
    to a GPIO pin and may instead be interfaced through an ADC or I2C).

    This is an abstract base class. The subclasses InputPin and
    OutputPin extend Pin into a usable form.
    """
    _PIGPIO_MODES = {'INPUT': 0,
                     'OUTPUT': 1,
                     'ALT5': 2,
                     'ALT4': 3,
                     'ALT0': 4,
                     'ALT1': 5,
                     'ALT2': 6,
                     'ALT3': 7}

    def __init__(self, pin, pig=None):
        """ Inherits attributes and methods from IODeviceBase.
        """
        super().__init__(pig)
        self.pin = pin

    @property
    def mode(self):
        """ The currently active pigpio mode of the pin.
        """
        return dict(map(reversed, self._PIGPIO_MODES.items()))[self.pig.get_mode(self.pin)]

    @mode.setter
    def mode(self, mode):
        """
        Performs validation on requested mode, then sets the mode.
        Raises runtime error if something goes wrong.
        """
        if mode not in self._PIGPIO_MODES.keys():
            raise ValueError("Pin mode must be one of: {}".format(self._PIGPIO_MODES.keys()))
        result = self.pig.set_mode(self.pin, self._PIGPIO_MODES[mode])

        # Pull error and print it
        if result != 0:
            raise RuntimeError('Failed to write mode {} on pin {}'.format(mode, self.pin))

    def toggle(self):
        """ If pin is on, turn it off. If it's off, turn it on. Do not
        raise a warning when pin is read in this way.
        """
        self.write(not self.read())

    def read(self):
        """ Returns the value of the pin: usually 0 or 1 but can be
        overridden e.g. by PWM which returns duty cycle.
        """
        self.pig.read(self.pin)

    def write(self, value):
        """ Sets the value of the Pin. Usually 0 or 1 but behavior
        differs for some subclasses.
        """
        if value not in (0, 1):
            raise ValueError('Cannot write a value other than 0 or 1 to a Pin')
        self.pig.write(self.pin, value)


class PWMOutput(Pin):
    """
    I am a Special Pin!
    """
    _DEFAULT_FREQUENCY = 20000
    _DEFAULT_SOFT_FREQ = 2000
    _HARDWARE_PWM_PINS = (12, 13, 18, 19)

    def __init__(self, pin, initial_duty=0, frequency=None, pig=None):
        super().__init__(pin, pig)
        if pin not in self._HARDWARE_PWM_PINS:
            self.hardware_enabled = False
            frequency = self._DEFAULT_SOFT_FREQ if frequency is None else frequency
            raise RuntimeWarning(
                'PWMOutput called on pin {} but that is not a PWM channel. Available frequencies will be limited.'.format(
                    self.pin))
        else:
            self.hardware_enabled = True
            frequency = self._DEFAULT_FREQUENCY if frequency is None else frequency
        self.__pwm(frequency, initial_duty)

    @property
    def frequency(self):
        """ Return the current PWM frequency active on the pin.
        """
        return self.pig.get_PWM_frequency(self.pin)

    @frequency.setter
    def frequency(self, new_frequency):
        """ Description:
        Note: pigpio.pi.hardware_PWM() returns 0 if OK and an error code otherwise.
        - Tries to write hardware PWM if hardware_enabled
        - If that fails, or if not hardware_enabled, tries to write software PWM instead."""
        self.__pwm(new_frequency, self._duty())

    @property
    def duty(self):
        """ Description:
        Returns the PWM duty cycle (pulled straight from pigpiod) mapped to the range [0-1] """
        return self.pig.get_PWM_dutycycle(self.pin) / self.pig.get_PWM_range(self.pin)

    def _duty(self):
        """ Returns the pigpio int representation of the duty cycle
        """
        return self.pig.get_PWM_dutycycle(self.pin)

    @duty.setter
    def duty(self, duty_cycle):
        """ Description:
        Validation of requested duty cycle is performed here.
        Sets the PWM duty cycle to a value proportional to the input between (0, 1) """
        if not 0 <= duty_cycle <= 1:
            raise ValueError('Duty cycle must be between 0 and 1')
        self.__pwm(self.frequency, int(duty_cycle * self.pig.get_PWM_range(self.pin)))

    def read(self):
        """Overloaded to return duty cycle instead of reading the value on the pin """
        return self.duty

    def write(self, value):
        """Overloaded to write duty cycle"""
        self.duty = value

    def on(self):
        """ Same functionality as parent, but done with PWM intact"""
        self.duty = 1

    def off(self):
        """ Same functionality as parent, but done with PWM intact"""
        self.duty = 0

    def __pwm(self, frequency, duty):
        """ Description:
        -If hardware_enabled is True, start a hardware pwm with the requested duty.
        -Otherwise (or if setting a hardware pwm fails and hardware_enabled is write to False),
         write a software pwm in the same manner."""
        if self.hardware_enabled:
            self.__hardware_pwm(frequency, duty)
        if not self.hardware_enabled:
            self.__software_pwm(frequency, duty)

    def __hardware_pwm(self, frequency, duty):
        """ Description:
        -Tries to write a hardware pwm. result == 0 if it suceeds.
        -Sets hardware_enabled flag to indicate success or failure"""
        # print('pin: %3.0d freq: %5.0d duty: %4.2f'%(self.pin,frequency,duty))
        result = self.pig.hardware_PWM(self.pin, frequency, duty)
        if result != 0:
            self.hardware_enabled = False
            raise RuntimeWarning(
                'Failed to start hardware PWM with frequency {} on pin {}. Error: {}'.format(frequency, self.pin,
                                                                                             self.pig.error_text(
                                                                                                 result)))
        else:
            self.hardware_enabled = True

    def __software_pwm(self, frequency, duty):
        """ Used for pins where hardware PWM is not available. """
        self.pig.set_PWM_dutycycle(self.pin, duty)
        realized_frequency = self.pig.set_PWM_frequency(self.pin, frequency)
        if frequency != realized_frequency:
            raise RuntimeWarning(
                'A PWM frequency of {} was requested but the best that could be done was {}'.format(frequency,
                                                                                                    realized_frequency))
        self.hardware_enabled = False