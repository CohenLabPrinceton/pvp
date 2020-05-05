from abc import ABC

from vent.io.devices.pins import Pin, PWMOutput


class SolenoidBase(ABC):
    """ An abstract baseclass that defines methods using valve terminology.
    Also allows configuring both normally _open and normally closed valves (called the "form" of the valve).
    """
    _FORMS = {'Normally Closed': 0,
              'Normally Open': 1}

    def __init__(self, form='Normally Closed'):
        self.form = form

    @property
    def form(self):
        """ Returns the human-readable form of the valve
        """
        return dict(map(reversed, self._FORMS.items()))[self._form]

    @form.setter
    def form(self, f):
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
            self.write(0)
        else:
            self.write(1)

    def close(self):
        """ De-energizes valve if Normally Closed. Energizes if
        Normally Open"""
        if self.form == 'Normally Closed':
            self.write(0)
        else:
            self.write(1)


class OnOffValve(SolenoidBase, Pin):
    """ An extension of vent.io.iobase.Pin which uses valve terminology for its methods.
    Also allows configuring both normally _open and normally closed valves (called the "form" of the valve).
    """
    _FORMS = {'Normally Closed': 0,
              'Normally Open': 1}

    def __init__(self, pin, form='Normally Closed', pig=None):
        self.form = form
        Pin.__init__(self, pin, pig)
        SolenoidBase.__init__(self, form=form)

    @property
    def isopen(self):
        """ The status of the valve.

        Returns:
            Bool: True if _open, False if closed.
        """
        return True if self.read() else False


class PWMControlValve(SolenoidBase, PWMOutput):
    """ An extension of PWMOutput which incorporates linear
    compensation of the valve's response.
    """

    def __init__(self, pin, form='Normally Closed', initial_duty=0, frequency=None, pig=None):
        PWMOutput.__init__(self, pin=pin, initial_duty=initial_duty, frequency=frequency, pig=pig)
        SolenoidBase.__init__(self, form=form)

    @property
    def setpoint(self):
        """ The linearized setpoint corresponding to the current duty cycle according to the valve's response curve

        Args:
            self:

        Returns:

        """
        return self.inverse_response(self.duty)

    @setpoint.setter
    def setpoint(self, setpoint):
        """Overridden to determine & write the duty cycle corresponting
        to the requested linearized setpoint according to the valve's
        response curve"""
        self.duty = self.response(setpoint)

    def response(self, setpoint):
        """Setpoint takes a value in the range (0,100) so as not to
        confuse with duty cycle, which takes a value in the range (0,1).
        Response curves are specific to individual valves and are to
        be implemented by subclasses. If not implemented in subclass,
        defaults to a perfectly linear response"""
        return setpoint / 100

    def inverse_response(self, duty_cycle):
        """Inverse of response. Given a duty cycle in the range (0,1),
        returns the corresponding linear setpoint in the range (0,100).
        """
        return duty_cycle * 100


class SimOnOffValve(SolenoidBase):
    """ stub: a simulated on/off valve"""

    def __init__(self, pig=None):
        self.state = 0

    def open(self):
        self.state = 1

    def close(self):
        self.state = 0

    @property
    def isopen(self):
        return True if self.state else False


class SimControlValve(SolenoidBase):
    """stub: a simulated linear control valve"""

    def __init__(self, pig=None):
        self._setpoint = 0

    @property
    def setpoint(self):
        """ The requested linearized set-point of the valve.

        Returns:

        """
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value):
        """

        Args:
            value: A float between 0 and 1; the requested set-point of the valve as a proportion of maximum

        """
        if not 0 <= value <= 1:
            raise ValueError('Setpoint must be in [0, 1]')
        else:
            self._setpoint = value
