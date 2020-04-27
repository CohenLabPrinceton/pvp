from iobase import OutputPin, PWMOutput
'''
Class definitions for specific actuators / output devices
'''

class Solenoid(OutputPin):
	def __init__(self):
		pass

class ProportionalValve(PWMOutput,Solenoid): 
	# or DAC out if it comes to that
	def __init__(self):
		pass
