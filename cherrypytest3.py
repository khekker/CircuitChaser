#!/usr/bin/env python
# -*- coding: utf-8 -*-

# string.Template requires Python 2.4+
import string
from string import Template
import os
os.chdir("/home/pi/pythonprogs")
import cherrypy
import time,datetime
import socket
#import commands
import sqlite3
from subprocess import check_output

__author__ = 'Dan McDougall <YouKnowWho@YouKnowWhat.com>'
#Modified by Keith Hekker 2014-2015

# Trying to cut down on long lines...
jquery_url = 'http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js'
jquery_ui_url = 'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js'
jquery_ui_css_url = \
'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/themes/black-tie/jquery-ui.css'


class Comet(object):
	@cherrypy.expose
	def index(self):
		f = open('RaceScore.htm')
		tempText = f.read()
		f.close()
		html = Template(tempText)
		page = html.substitute(
            jquery_ui_css_url=jquery_ui_css_url,
            jquery_url=jquery_url,
            jquery_ui_url=jquery_ui_url)
		#print cherrypy.request.remote.ip
		return page

	@cherrypy.expose
	def ping(self, **kw):
		"""Start a loop to report data and stream the output"""
		def run_command():
			dLastFileUpdate = 0
			lStart = True
			ThisIpAddress = ""
			while True:
				now = datetime.datetime.now()
				cTime = str(now)[:22]
				(mode,ino,dev,nlink,uid,gid,size,atime,mtime,ctime) = os.stat("output.txt")
				dNewFileUpdate = mtime
				if dNewFileUpdate > dLastFileUpdate:
					for x in range(1,10):
						#print x
						cTxtOutFile = open("output.txt","r")			
						cOut = ""
						for line in cTxtOutFile:
							cOut = cOut + line
						#print cOut
						cTxtOutFile.close()
						if len(cOut) > 10:
							break
						else:
							time.sleep(.1)
					if lStart == True:
						ThisIpAddress = check_output(['hostname','-I'])
						ThisIpAddress = string.rstrip(ThisIpAddress)
						print "IP Address = " + ThisIpAddress
						lStart = False
								
					#Brute force seconds since midnight calculation
					aTime = str(datetime.datetime.now())[:22][11:].split(":")
					TotalSecondsSinceMidnight = int(aTime[0])*3600 + int(aTime[1])*60 + float(aTime[2])
					#print TotalSecondsSinceMidnight	
					cServerTime = "<div id='ServerTime' style='display:none'>" + str(TotalSecondsSinceMidnight) + "</div>"
					cIpAddress = "<div id='IpAddress' style='display:none'>Circuit Chaser at " + ThisIpAddress + ":8080</div>"
					yield '<script>parent.UpdateProgress("' + cOut + cServerTime + cIpAddress + '")</script>'
					dLastFileUpdate = dNewFileUpdate
				time.sleep(.25)
				
		return run_command()
        
	# Enable streaming for the ping method.  Without this it won't work.
	ping._cp_config = {'response.stream': True}

	@cherrypy.expose
	def kill_proc(self, **kw):
		"""Kill the process """
		return "<strong>Success:</strong> The process was stopped successfully."

	@cherrypy.expose
	def Race_Admin(self, **kw):
		cLastActionPerformed = kw.get('cLastActionPerformed','')
		f = open('RaceAdmin.htm')
		tempText = f.read()
		f.close()
		HTMLOut = Template(tempText)
		PseudonymCardsAvailable = self.CreatePseudonymPhrase()
		d = dict(LastName='',FirstName='',Userid='',PlayerMatchTable='',PlayerHandle='',PseudonymCardsAvailable=PseudonymCardsAvailable,cLastActionPerformed=cLastActionPerformed)	
		return HTMLOut.safe_substitute(d)

	@cherrypy.expose
	def PlayerEdit(self, **kw):
		cLastName = kw.get('LastName',"")
		cFirstName = kw.get('FirstName',"")
		PlayerMatchTableHeader = "<form name='PlayerSelection' method='post' action='SelectPlayer'><p style='font-weight:bold'>Results:</p>"
		PlayerMatchTableHeader +="<Table id='PlayerMatchTable' border='1'><TR><TH style='width:150px'>Last Name</th><TH style='width:150px'>First Name</th><TH style='width:150px'>Change Handle (optional)</th><TH style='width:100px'>Tag To Use</th><TH style='width:100px'>Permanent Link</th><th>Select?</th></tr>"
		conn = sqlite3.connect('SpeedTimer.db')
		cur = conn.cursor()
		rows = cur.execute("select alternate from Pseudonym where alternate not NULL group by card_id")
		data = cur.fetchall()

		CardToAssign = ""
		if (len(data) != 0):
			for x in range(0,len(data)):
				CardToAssign+= "<option value='" + data[x][0]+ "'>" + data[x][0] + "</option>"
				
		if (not cFirstName):
			rows = cur.execute("select last_name,first_name,user_id from Players where last_name == ? order by last_name",(cLastName,))
			PlayerMatchTable = PlayerMatchTableHeader + "<TR><TD>" + cLastName + "</td><TD><input id='FirstName1' name='firstname' type='text' value=''></td><td><input id='1' name='handle' type='text' value=''></td><td><select id='Select1' name='Cards1'>" + CardToAssign + "</select></td><td><select id='Perm1' name='Perm'><option value='No'>No</option><option value='Yes'>Yes</option></select></td><td><input id='Search' name='Select' type='button' value='Select' onClick='SelectPlayer(1)'/></td></tr>"
			extra_counter = 2
		else:
			rows = cur.execute("select last_name,first_name,user_id from Players where last_name == ? and first_name == ? order by last_name,first_name",(cLastName,cFirstName))
			PlayerMatchTable = PlayerMatchTableHeader + "<TR><TD>" + cLastName + "</td><TD>" + cFirstName + "</td><td><input id='1' name='handle' type='text' value=''></td><td><select id='Select1' name='Cards1'>" + CardToAssign + "</select></td><td><select id='Perm1' name='Perm'><option value='No'>No</option><option value='Yes'>Yes</option></select></td><td><input id='Search' name='Select' type='button' value='Select' onClick='SelectPlayer(1)'/></td></tr>"
			extra_counter = 2
		data = cur.fetchall()
				
		for x in range(0,len(data)):
			if (cLastName.lower() == data[x][0].lower() and cFirstName.lower() == data[x][1].lower()):
				PlayerMatchTable = PlayerMatchTableHeader + "<TR><TD>" + cLastName + "</td><TD>" + cFirstName + "</td><td><input id='1' name='handle' type='text' value='" + data[x][2] + "'></td><td><select id='Select1' name='Cards1'>" + CardToAssign + "</select></td><td><select id='Perm1' name='Perm'><option value='No'>No</option><option value='Yes'>Yes</option></select></td><td><input id='Search' name='Select' type='button' value='Select' onClick='SelectPlayer(1)'/></td></tr>"
				continue
			cTableRowContents = "<TR><TD>" + data[x][0] + "</td><TD>" + data[x][1] + "</td><TD><input id='" + str(x + extra_counter) + "' name='handle' type='text' value='" + data[x][2] + "'></td><td><select id='Select" + str(x + extra_counter) + "' name='Cards" + str(x + extra_counter) + "'>" + CardToAssign + "</select></td><td><select id='Perm" + str(x + extra_counter) + "' name='Perm'><option value='No'>No</option><option value='Yes'>Yes</option></select></td><td><input name='select' type='button' value='Select' onClick='SelectPlayer(" + str(x + extra_counter) + ")'/></td></tr>"
			rows = cur.execute("select Pseudonym.alternate from CardAssigned,Pseudonym where CardAssigned.card_id == Pseudonym.card_id and handle  = ? order by datetime desc limit 1",(data[x][2],))
			qresult = cur.fetchall()
			if (len(qresult) != 0):
				cTableRowContents = cTableRowContents.replace('>' + qresult[0][0],' selected>' + qresult[0][0])
			PlayerMatchTable += cTableRowContents
		PlayerMatchTable += "</table> <input type='hidden' name='SelectedPlayer' value=''> </form>"
		if (len(data) == 0):
			cLastActionPerformed = "<div class='boxed' style='color:red;'>Player not found: enter new handle, choose card, then click 'Select' to enter player in database. Or, search again...</div><br />"
		else:
			cLastActionPerformed = "<div class='boxed'>Existing player(s) found: review handle, choose card, then click 'Select' to enable player to participate again</div><br />"
		conn.close()
		
		f = open('RaceAdmin.htm')
		tempText = f.read()
		f.close()
		HTMLOut = Template(tempText)
		PseudonymCardsAvailable = self.CreatePseudonymPhrase()
		d = dict(LastName=cLastName,FirstName=cFirstName,PlayerMatchTable=PlayerMatchTable,CardToAssign=CardToAssign,PlayerHandle='',PseudonymCardsAvailable=PseudonymCardsAvailable,cLastActionPerformed=cLastActionPerformed)
		return HTMLOut.safe_substitute(d)
		
	@cherrypy.expose
	def SelectPlayer(self, **kw):
		#for key, value in kw.iteritems():
		#	print "%s = %s" % (key, value)
		#print kw.get('LastName','')
		
		#Still need to test for length array here.
		aPlayerName = kw.get('SelectedPlayer',"").split("%")
		cLastName = aPlayerName[0]
		if (cLastName == ""):
			return "Error: No last name received"
		cFirstName = aPlayerName[1]
		if (cFirstName == ""):
			return "Error: No first name received"
		PlayerHandle = aPlayerName[2]
		cCardSelected = aPlayerName[3]
		cPermanentLink = aPlayerName[4]
		if (cPermanentLink == "Yes"):
			lPermanentLink = 1
		else:
			lPermanentLink = 0	
		
		now = datetime.datetime.now()
		cTime = str(now)[:22]
		conn = sqlite3.connect('SpeedTimer.db')
		cur = conn.cursor()
		rows = cur.execute("select last_name,first_name,user_id,user_number from Players where last_name == ? and first_name == ? order by last_name, first_name",(cLastName,cFirstName))
		data = cur.fetchall()
		# If Player not found in Players table
		if (len(data) == 0):
			rows = cur.execute("select MAX(user_number) from Players")
			data = cur.fetchall()
			if (data[0][0] == None):
				cPlayerNumber = "00001"
			else:
				cPlayerNumber = str(int(data[0][0])+1).zfill(5)
			cur.execute("insert into Players(last_name,first_name,user_id,user_number,dt_created,permanent) values(?,?,?,?,?,?)",(cLastName,cFirstName,PlayerHandle,cPlayerNumber,cTime,lPermanentLink))
			cLastActionPerformed = "New player " + cFirstName + " " + cLastName + " created and is ready for play using the handle " + PlayerHandle + " and Tag " + cCardSelected + "..."
		else:
			if (not PlayerHandle):
				PlayerHandle = "&nbsp;"
			cPlayerNumber = data[0][3]
			cur.execute("update Players set user_id = ?, permanent = ? where user_number == ?",(PlayerHandle,lPermanentLink,cPlayerNumber))
			cLastActionPerformed = "Existing player " + cFirstName + " " + cLastName + " has handle " + PlayerHandle + " and is ready for play using Tag " + cCardSelected + "..."
		conn.commit()
		rows = cur.execute("select card_id from Pseudonym where alternate == ?",(cCardSelected,))
		data = cur.fetchall()
		if (len(data) == 0):
			Cardid = "Error"
		else:
			Cardid = data[0][0]
			
		cur.execute("insert into CardAssigned(card_id,handle,player_number,datetime) values (?,?,?,?)",(Cardid,PlayerHandle,cPlayerNumber,cTime))
		conn.commit()
		conn.close()
		cLastActionPerformed = "<div class='boxed'>" + cLastActionPerformed + "</div><br />"
		x= self.Race_Admin(cLastActionPerformed=cLastActionPerformed)
		return x
		
	@cherrypy.expose
	def AssignPseudonym(self, **kw):
		aCardId = kw.get('Cards',"").split("|")
		cCardId = "".join(aCardId[0].split())
		#cCardId = aCardId[0]
		cPseudonym = kw.get('Pseudonym',"")
		conn = sqlite3.connect('SpeedTimer.db')
		cur = conn.cursor()
		rows = cur.execute("select * from Pseudonym where card_id == ?",(cCardId,))
		data = cur.fetchall()	
		if (len(data) == 0):
			cur.execute("insert into Pseudonym (card_id,alternate) values (?,?)",(cCardId,cPseudonym))
		else:
			cur.execute("update Pseudonym set alternate = ?  where card_id = ?",(cPseudonym,cCardId))
		conn.commit()
		conn.close()
		cLastActionPerformed = "<div class='boxed'>Pseudonym " + cPseudonym + " set for Card " + cCardId + "</div><br />"
		x = self.Race_Admin(cLastActionPerformed=cLastActionPerformed)
		return x
		
	def CreatePseudonymPhrase(self):
		conn = sqlite3.connect('SpeedTimer.db')
		cur = conn.cursor()
		rows = cur.execute("select card_id,start from Timer where card_id not in (select card_id from Pseudonym) group by card_id ORDER BY start DESC limit 100")
		data = cur.fetchall()
		if (len(data) != 0):			
			for x in range(0,len(data)):
				#Detecting whether we are looking at a card which will (probably) contain numbers
				#This may fail in the future....depending on card ids
				if (data[x][0][:2].isdigit() == False):
					continue
				rows = cur.execute("insert into Pseudonym (card_id) values (?)",(data[x][0],))
			conn.commit()
		rows = cur.execute("select * from Pseudonym")
		data = cur.fetchall()
		conn.close()
		PseudonymCardsAvailable = ""
		if (len(data) != 0):
			for x in range(0,len(data)):
				cAlternate = data[x][1] if data[x][1] != None else ""
				PseudonymCardsAvailable += "<option value='" + data[x][0] + "'>" + data[x][0] + " | " + cAlternate + "</option>"
		return PseudonymCardsAvailable
		
		
cherrypy.config.update({
    'log.screen':True,
    'tools.sessions.on': True,
    'checker.on':False,
    'server.socket_host':'0.0.0.0',
    'tools.staticdir.root': '/home/pi/pythonprogs',
    'tools.staticdir.on': True,
    'tools.staticdir.dir':'static'})
    
cherrypy.tree.mount(Comet(), config=None)
cherrypy.engine.start()
cherrypy.engine.block()
