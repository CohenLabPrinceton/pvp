import RPi.GPIO as GPIO
import time

time.sleep(0.1)
SAMPLETIME = 0.5

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)

i = 0
while i < 10:
    GPIO.output(17, GPIO.HIGH)

    time.sleep(SAMPLETIME)

    #GPIO.output(17, GPIO.LOW)    
    GPIO.output(27, GPIO.HIGH)

    time.sleep(SAMPLETIME)

    #GPIO.output(27, GPIO.LOW)
    i = i + 1

GPIO.cleanup()
