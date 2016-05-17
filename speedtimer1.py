#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path = sys.path + ['nfcpy']
import os
os.chdir("/home/pi/pythonprogs")

import nfc
import sqlite3
import datetime
import RPi.GPIO as GPIO

import time
from time import sleep


conn = sqlite3.connect('SpeedTimer.db')
cur = conn.cursor()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12,GPIO.OUT)

#nAllTimeSlowestTime = 0
#nTodaysSlowestTime = 0

#def UpdateAllTimeTopTen(**kw):
#	if nAllTimeSlowestTime == 0:
		#if nAllTimeSlowestTime = 0, that means that this application is just
		#starting up, so we need to run a query to find the top ten.
#		rows = cur.execute("select * from Timer order by start desc limit 10")
#		data = cur.fetchall()
#	cCardId = kw.get('cCardId',"")
#	if (cCardId == ""):
		
#```````````````````````````````````def UpdateTodaysTopTen(**kw):
print "Starting Speed Timer..."
	
def connected(tag):
	#sample tag Type2Tag ATQ=4400 SAK=00 UID=0419bde2852a80
	#print tag
	GPIO.output(12,0)
	dCurrentTime = datetime.datetime.now()
	cCurrentTime = str(datetime.datetime(dCurrentTime.year,dCurrentTime.month,dCurrentTime.day,dCurrentTime.hour,dCurrentTime.minute,dCurrentTime.second,dCurrentTime.microsecond))[:23]
	s = str(tag)
	#print s
	start_id = s.find('UID=') + 4
	cCardid = s[start_id:start_id + 14]
	#Checking to see if card pseudonym is MasterCard. If so, shut down requested.
	rows = cur.execute("select alternate from Pseudonym where card_id = ?",(cCardid,))
	data = cur.fetchall()	
	try:
		cCardPseudonym = data[0][0]
	except:
		cCardPseudonym = "NotFound"	
	try:	
		cCardPseudonym = cCardPseudonym.upper()
	except:
		cCardPseudonym = "NotFound"	
	if cCardPseudonym == "MASTERCARD":
		#The following lines (adding some text to the output file) are here to
		#trigger the hdmipionoff script to turn the HDMIPi on (if it is off).
		#If this is not done, then there is a chance that the HDMIPi will be in 'off' state
		#when the Pi is rebooted and, furthermore HDMI output 1 is selected for output rather than
		#HDMI output 2, which is what the Pi is connected to.
		with open("output.txt","a") as outputfile:
			outputfile.write("<BR>")
			outputfile.close()
		print "Shut down message received, bailing...."
		sleep(7)
		os.system("sudo shutdown -h -P now") # shuts down Pi			
		quit()
	rows = cur.execute("select card_id,handle,player_number from CardAssigned where card_id = ? order by datetime desc limit 1",(cCardid,))
	data = cur.fetchall()
	#Picking up the player's handle and player number
	if (len(data) != 0):
		cCardid = data[0][1]
		cPlayerNumber = data[0][2]
	else:
		cPlayerNumber = "NotAssigned"	
	rows = cur.execute("select * from Timer order by start desc limit 10")
	data = cur.fetchall()
	if len(data) == 0: 
		StartTime = cCurrentTime[11:23]
		EndTime = "&nbsp;" #&nbsp;&nbsp;<IMG SRC='712.GIF' height='42' width='42'>"
		TimeElapsed = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
		cur.execute('''INSERT INTO Timer(card_id,player_number,start) VALUES(?,?,?)''',(cCardid,cPlayerNumber,cCurrentTime))
		conn.commit()
		cTxtOutFile = open("output.txt","w")
		cTxtOutFile.write("<table border=1><TR><TH>Card/Name</th><TH>Start</th><TH>End</th><TH>Time Elapsed</th></tr>")
		cTxtOutFile.write("<TR><TD>" + cCardid + "</td><td>" + StartTime + "</td><td>" + EndTime + "</td><td>" + TimeElapsed + "</td></tr></table>")
		cTxtOutFile.close()
		GPIO.output(14,0)
		return True
	else:
		lCardidFound = False
		lIsThisFinishTime = False
		for x in range(0,len(data)):
			#print data[0]
			if (x == 0):
				cLastEntry = max(data[x][1],data[x][2])
				dLastEntry = datetime.datetime.strptime(cLastEntry,"%Y-%m-%d %H:%M:%S.%f")
				dOneSecondAgo = datetime.datetime.now() - datetime.timedelta(seconds=1)
				if (dLastEntry > dOneSecondAgo):
					#print "Ignoring reading as too close to previous..."
					return True
				else:
					GPIO.output(12,1)
			if (cCardid == data[x][0] and lCardidFound == False):
				lCardidFound = True 
				cCurrentCard = cCardid
				if (data[x][2] is None): #Finish time not filled in yet
					cStartTime = data[x][1]
					cur.execute("update timer set finish = '" + cCurrentTime + "' where start == '" + cStartTime + "'")
					lIsThisFinishTime = True
	
	if lIsThisFinishTime == False:
		cur.execute('''INSERT INTO Timer(card_id,player_number,start) VALUES(?,?,?)''',(cCardid,cPlayerNumber,cCurrentTime))

	conn.commit()	
	#if lIsThisFinishTime == True:
	#	if cCurrentTime < nAllTimeSlowestTime:
	#		UpdateAllTimeTopTen(cCardid,cPlayerNumber,cCurrentTime)
		
	
	cTxtOutFile = open("output.txt","w")
	cTxtOutFile.write("<table id='DataTable' border=1><TR><TH>Card/Name</th><TH>Start</th><TH>End</th><TH>Time Elapsed</th></tr>")
	rows = cur.execute("select * from Timer order by start desc limit 11")
	data = cur.fetchall()
	lCurrentCardFound = False
	for x in range(0,len(data)):
		cCurrentCard = data[x][0]
		if (cCurrentCard == cCardid and lCurrentCardFound == False):
			cSetColor = "RED"
			lCurrentCardFound = True
		else:
			cSetColor = "BLACK"	
		StartTime = data[x][1][11:23]
		if (data[x][2] is None):
			#Finish time hasn't been filled in yet.
			cStartTime = data[x][1]
			dStartTime = datetime.datetime.strptime(cStartTime,"%Y-%m-%d %H:%M:%S.%f")
			EndTime = "&nbsp;" #"&nbsp;&nbsp;&nbsp;<IMG SRC='712.GIF' height='42' width='42'>"
			TimeElapsed = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
			#TimeElapsed = str(datetime.datetime.now() - dStartTime) 
		else:
			cStartTime = data[x][1]
			EndTime =  data[x][2][11:23]
			cEndTime = data[x][2]
			dStartTime = datetime.datetime.strptime(cStartTime,"%Y-%m-%d %H:%M:%S.%f")
			dEndTime = datetime.datetime.strptime(cEndTime,"%Y-%m-%d %H:%M:%S.%f")
			TimeElapsed = str(dEndTime - dStartTime)[:-3]
			if (TimeElapsed[1] == ":"):
				TimeElapsed = "0" + TimeElapsed
		cTxtOutFile.write("<TR STYLE='color:" + cSetColor + "'><TD>" + cCurrentCard + "</td><td>" + StartTime + "</td><td>" + EndTime + "</td><td>" + TimeElapsed.zfill(12) + "</td></tr>")	
	cTxtOutFile.write("</table>")	
	cTxtOutFile.close()
	time.sleep(.4)
	GPIO.output(12,0)
	#Changed the value of the following line from True to False to allow closing of the communication with the tag 2016/01/17
	return False
	
	
print "Attempting to open contactless front end..."	
while True:
	try:
		clf = nfc.ContactlessFrontend('tty:AMA0:pn53x')
		print "Success..!"
		break
	except IOError as error:
		if error.errno != 19:
			raise error
		print "Attempting to open contactless front end (retrying)..."
		time.sleep(1.0)
		continue
       	
#clf = nfc.ContactlessFrontend('tty:AMA0:pn53x')
while True:
	clf.connect(rdwr={'on-connect':connected})
GPIO.cleanup()
