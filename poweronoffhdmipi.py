#!/usr/bin/env python2.7  
# HDMIPi_toggle.py by Alex Eames http://raspi.tv/?p=7540 
# Modified by Keith Hekker, December 15, 2015
import RPi.GPIO as GPIO
import os,time
from time import sleep

os.chdir("/home/pi/pythonprogs")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(22, GPIO.IN)


# If 22 is set as an input, the hardware pullup on the HDMIPi board 
# keeps value at HIGH. We only change the port to an output when we 
# want to toggle the button. 
# This is because, when set as an output, the HDMIPi buttons are disabled.
# So each time we toggle the HDMIPi on or off, we set port back to input


def toggle():
    GPIO.setup(22, GPIO.OUT, initial=1)
    GPIO.output(22, 0)         # this is our simulated button press
    sleep(0.2)                 # hold button for 0.2 seconds
    GPIO.output(22, 1)         # release button
    GPIO.setup(22, GPIO.IN)    # set port back to input (re-enables buttons)

lMonitorOn = True
print "Starting, going to sleep for half an hour..."
sleep(1800)
while True:
	(mode,ino,dev,nlink,uid,gid,size,atime,sNewFileUpdate,ctime) = os.stat("output.txt")
	sCurrentTime = time.time()
	if lMonitorOn == True:
		if (sNewFileUpdate  + 600) < sCurrentTime:
			#print sNewFileUpdate + 600 
			#print sCurrentTime
			#print (sNewFileUpdate  + 600) - sCurrentTime
			print "Turning monitor off...."
			toggle()
			lMonitorOn = False
			print lMonitorOn
		sleep(5)	
	else:
		if sNewFileUpdate > (sCurrentTime - 600):
			#print sCurrentTime - 600 
			#print sCurrentTime
			#print (sCurrentTime - 600) - sNewFileUpdate
			print "Turning monitor on...."
			toggle()
			lMonitorOn = True 
		sleep(5)

#print "finished, cleaning up"
GPIO.cleanup()
