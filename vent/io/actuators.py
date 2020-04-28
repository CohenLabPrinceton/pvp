from .iobase import OutputPin, PWMOutput
'''
Class definitions for specific actuators / output devices
'''

class SolenoidValve(OutputPin):
	_FORMS = {	'Normally Closed' 	: 0,
				'Normally Open'		: 1 }
	def __init__( self, pin, form='Normally Closed', pig=None ):
		self.form = self._FORMS[form]
		super().__init__(pin,pig)
	
	@property
	def form(self):
		'''Returns the human-readable form of the valve '''
		return map(reversed,self._FORMS.items())[ self._form ]
		
	@form.setter
	def form(self,f):
		if f not in self._FORMS:
			raise ValueError('form must be either NC for Normally Closed or NO for Normally Open')
		else: self._form = self._FORMS[f]
	
	def open(self):
		''' 
		-Energizes valve if Normally Closed. 
		-De-energizes if Normally Open'''
		if self._form: self.off()
		else: self.on()
		
	def close(self):
		''' 
		-De-energizes valve if Normally Closed. 
		-Energizes if Normally Open'''
		if not self._form: self.off()
		else: self.on()

class PWMControlValve(PWMOutput): 
	# or DAC out if it comes to that
	def __init__(self,pin,form='Normally Closed',initial_duty=0,frequency=None,pig=None):
		super().__init__(pin,initial_duty,frequency,pig)
		self.last
		
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
