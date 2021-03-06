#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import wx
import requests
import time
import subprocess
import os
import wx
import re
import sys
import time
import itertools
import hashlib
import tempfile
import zipfile
import shutil
import base64
from uuid import getnode as get_mac
import wx.lib.newevent
import thread
import exceptions


ID_ONE = 1
ID_TWO = 2
ID_THREE = 3

import socket, struct
url = "http://23.239.29.14:8000"
#url = "http://localhost:8000"

(RunEvent, EVT_RUN) = wx.lib.newevent.NewEvent()
(CancelEvent, EVT_CANCEL) = wx.lib.newevent.NewEvent()
(DoneEvent, EVT_DONE) = wx.lib.newevent.NewEvent()
(ProgressStartEvent, EVT_PROGRESS_START) = wx.lib.newevent.NewEvent()
(ProgressEvent, EVT_PROGRESS) = wx.lib.newevent.NewEvent()

class InterruptedException(exceptions.Exception):
    def __init__(self, args = None):
        self.args = args

class ThreadedJob:
	def __init__(self):
		# tell them ten seconds at first
		self.secondsRemaining = 10.0
		self.lastTick = 0

		# not running yet
		self.isPaused = False
		self.isRunning = False
		self.keepGoing = True
#		self.secondsPerTick = 0
	def Start(self):
		self.keepGoing = self.isRunning = True
		thread.start_new_thread(self.Run, ())
		self.isPaused = False

	def Stop(self):
		self.keepGoing = False

	def WaitUntilStopped(self):
		while self.isRunning:
			time.sleep(0.1)
		wx.SafeYield()

	def IsRunning(self):
		return self.isRunning

	def Run(self):
		# this is overridden by the
		# concrete ThreadedJob
		print "Run was not overloaded"
		self.JobFinished()
		pass

	def Pause(self):
		self.isPaused = True
		pass

	def Continue(self):
		self.isPaused = False
		pass

	def PossibleStoppingPoint(self):
		if not self.keepGoing:
			raise InterruptedException("process interrupted.")
		wx.SafeYield()

		# allow cancel while paused
		while self.isPaused:
			if not self.keepGoing:
				raise InterruptedException("process interrupted.")

		# don't hog the CPU
		time.sleep(0.1)

	def SetProgressMessageWindow(self, win):
		self.win = win


	def JobBeginning(self, totalTicks):
		self.lastIterationTime = time.time()
		self.totalTicks = totalTicks

		if hasattr(self, "win") and self.win:
			wx.PostEvent(self.win, ProgressStartEvent(total=totalTicks))

	def JobProgress(self, currentTick):
		dt = time.time() - self.lastIterationTime
		self.lastIterationTime = time.time()
		dtick = currentTick - self.lastTick
		self.lastTick = currentTick

		alpha = 0.92
		if currentTick > 1:
			self.secondsPerTick = dt * (1.0 - alpha) + (self.secondsPerTick * alpha)
		else:
			self.secondsPerTick = dt

		if dtick > 0:
			self.secondsPerTick /= dtick

			self.secondsRemaining = self.secondsPerTick * (self.totalTicks - 1 - currentTick) + 1

		if hasattr(self, "win") and self.win:
			wx.PostEvent(self.win, ProgressEvent(count=currentTick))

	def SecondsRemaining(self):
		return self.secondsRemaining


	def TimeRemaining(self):

		if 1: #self.secondsRemaining > 3:
			minutes = self.secondsRemaining // 60
			seconds = int(self.secondsRemaining % 60.0)
			return "%i:%02i" % (minutes, seconds)

		else:
			return "a few"

	def JobFinished(self):
		if hasattr(self, "win") and self.win:
			wx.PostEvent(self.win, DoneEvent())

		self.isRunning = False

class DownloadJob(ThreadedJob):
	""" A sample Job that demonstrates the mechanisms and features of the Threaded Job"""
	def __init__(self, file_name, link, title):
		self.src = file_name
		self.link = link
		self.title = title
		ThreadedJob.__init__(self)



	def Run(self):
		try:
			self.sudo_run()
		except Exception as e:
			print e


	def sudo_run(self):
		print "eneterd into sudo_run"
		self.time0 = time.clock()
		count = 0
		response = requests.get(self.link, stream=True)
	
		print response.headers

		"""
		if not response.headers.get("data-length"):
			print "here we have in dialog box"
			dlg = wx.MessageDialog(None, response.json().get("messege"), "Warning", wx.OK | wx.ICON_WARNING)
			dlg.ShowModal()
			dlg.Destroy()
			return     
		
		"""
		print "lenght of the content -length header %s"%response.headers.get("content-length")
		print "no error baby"
		total_length = int(response.headers.get('content-length'))
		
		print total_length
		block_size = 1024*100

		iter_length = total_length/block_size
		self.JobBeginning(iter_length)
		
		#zf = zipfile.ZipFile(self.src, mode='w')

		with open(self.src, 'wb') as zf:
			for data in range(iter_length+1):
				time.sleep(1)
				wx.Yield()
				#zf.fp.write(response.raw.read(block_size))  
				zf.write(response.raw.read(102400))  
				count += 1
				self.JobProgress(count)
				self.PossibleStoppingPoint()
			zf.close()	
		self.JobFinished()

	def __str__(self):
		""" The job progress dialog expects the job to describe its current state."""
		response = []
		if self.isPaused:
			response.append("Paused Counting")
		elif not self.isRunning:
			response.append("Will Count the seconds")
		else:
			response.append(self.title)
			
		return " ".join(response)

class UnZipJob(ThreadedJob):
	""" A sample Job that demonstrates the mechanisms and features of the Threaded Job"""
	def __init__(self, src, dist, hash_key, title):
		self.src = src
		self.dist = dist
		self.hash_key = hash_key
		self.title = title
		ThreadedJob.__init__(self)



	def Run(self):
		try:
			self.sudo_run()
		except Exception as e:
			print e


	def sudo_run(self):
		self.time0 = time.clock()
		zf = zipfile.ZipFile(self.src)

		uncompressed_size = sum((file_name.file_size for file_name in zf.infolist()))

		self.JobBeginning((len(zf.infolist())))
		extracted_size = 0
		count = 0
		for file_name, count in zip(zf.infolist(), range(len(zf.infolist()))):
			time.sleep(.5)
			wx.Yield()
			zf.extract(file_name, path = self.dist, pwd=self.hash_key)
			extracted_size += file_name.file_size
			self.JobProgress(count)
			count += 1
			self.PossibleStoppingPoint()

		self.JobFinished()

	def __str__(self):
		""" The job progress dialog expects the job to describe its current state."""
		response = []
		if self.isPaused:
			response.append("Paused Counting")
		elif not self.isRunning:
			response.append("Will Count the seconds")
		else:
			response.append(self.title)
			
		return " ".join(response)


class JobProgress(wx.Dialog):
	""" This dialog shows the progress of any ThreadedJob.
	It can be shown Modally if the main application needs to suspend 
	operation, or it can be shown Modelessly for background progressreporting.
	app = wx.PySimpleApp()
    
    	job = EggTimerJob(duration = 10)
	dlg = JobProgress(None, job)
	job.SetProgressMessageWindow(dlg)
	job.Start()
	dlg.ShowModal()

	"""
	def __init__(self, parent,  job):
		self.job = job

		wx.Dialog.__init__(self, parent, -1, size=(600,600), style=wx.STAY_ON_TOP)

		# vertical box sizer
		sizeAll = wx.BoxSizer(wx.VERTICAL)

		# Job status text
		self.JobStatusText = wx.StaticText(self, -1, "Starting...")
		sizeAll.Add(self.JobStatusText, 0, wx.EXPAND|wx.ALL, 8)

		# wxGague
		self.ProgressBar = wx.Gauge(self, -1, 10, wx.DefaultPosition, (500, 10))
		sizeAll.Add(self.ProgressBar, 0, wx.EXPAND|wx.ALL, 8)

		# horiz box sizer, and spacer to right-justify
		sizeRemaining = wx.BoxSizer(wx.HORIZONTAL)
		sizeRemaining.Add((2,2), 1, wx.EXPAND)

		# time remaining read-only edit
		# putting wide default text gets a reasonable initial layout.
		
		self.remainingText = wx.StaticText(self, -1, "???:??")
		sizeRemaining.Add(self.remainingText, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 8)

		# static text: remaining
		self.remainingLabel = wx.StaticText(self, -1, "remaining")
		sizeRemaining.Add(self.remainingLabel, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 8)


		#add that row to the mix
		sizeAll.Add(sizeRemaining, 1, wx.EXPAND)

		# horiz box sizer & spacer
		sizeButtons = wx.BoxSizer(wx.HORIZONTAL)
		sizeButtons.Add((2,2), 1, wx.EXPAND|wx.ADJUST_MINSIZE)

		# Pause Button
		#self.PauseButton = wx.Button(self, -1, "Pause")
		#sizeButtons.Add(self.PauseButton, 0, wx.ALL, 4)
		#self.Bind(wx.EVT_BUTTON, self.OnPauseButton, self.PauseButton)

		# Cancel button
		#self.CancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
		#sizeButtons.Add(self.CancelButton, 0, wx.ALL, 4)
		#self.Bind(wx.EVT_BUTTON, self.OnCancel, self.CancelButton)


		# Add all the buttons on the bottom row to the dialog
		sizeAll.Add(sizeButtons, 0, wx.EXPAND|wx.ALL, 4)

		self.SetSizerAndFit(sizeAll)
		sizeAll.SetSizeHints(self)

		# jobs tell us how they are doing
		self.Bind(EVT_PROGRESS_START, self.OnProgressStart)
		self.Bind(EVT_PROGRESS, self.OnProgress)
		self.Bind(EVT_DONE, self.OnDone)
		self.SetBackgroundColour("light blue")
		self.Layout()

	def OnPauseButton(self, event):
		if self.job.isPaused:
			self.job.Continue()
			self.PauseButton.SetLabel("Pause")
			self.Layout()
		else:
			self.job.Pause()
			self.PauseButton.SetLabel("Resume")
			self.Layout()

	def OnCancel(self, event):
		self.job.Stop()


	def OnProgressStart(self, event):
		self.ProgressBar.SetRange(event.total)
		self.statusUpdateTime = time.clock()

	def OnProgress(self, event):
		# update the progress bar
		self.ProgressBar.SetValue(event.count)
		self.remainingText.SetLabel(self.job.TimeRemaining())

		# update the text a max of 20 times a second
		if time.clock() - self.statusUpdateTime > 0.05:
			self.JobStatusText.SetLabel(str(self.job))
			self.statusUpdateTime = time.clock()
			self.Layout()

	def OnDone(self, event):
		self.ProgressBar.SetValue(0)
		self.JobStatusText.SetLabel("Finished")
		self.Destroy()

	
def Run_Unzip(src, dest, hash_key, title):
	app = wx.App(False)
	job = UnZipJob(src, dest, hash_key, title)
	dlg = JobProgress(None, job)
	job.SetProgressMessageWindow(dlg)
	job.Start()
	dlg.ShowModal()


def Run_Download(file_name, link, title):
	app = wx.App(False)
	job = DownloadJob(file_name, link, title)
	dlg = JobProgress(None, job)
	job.SetProgressMessageWindow(dlg)
	job.Start()
	dlg.ShowModal()

class Authentication(wx.Dialog):
	
	def __init__(self, parent, id=-1, title="Authentication Window"):
		wx.Dialog.__init__(self, parent, id, title, size=(-1, -1), style=wx.STAY_ON_TOP)
		
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.label = wx.StaticText(self, label="Enter Key:")
		self.field = wx.TextCtrl(self, value="", size=(300, 30))
		self.okbutton = wx.Button(self, label="Ok", id=wx.ID_OK)
		self.cancelbutton = wx.Button(self, label="Cancel", id=wx.ID_OK)

		self.mainSizer.Add(self.label, 0, wx.ALL, 8 )
		self.mainSizer.Add(self.field, 0, wx.ALL, 8 )

		self.buttonSizer.Add(self.okbutton, 0, wx.ALL, 8 )
		self.buttonSizer.Add(self.cancelbutton, 0, wx.ALL, 8 )

		self.mainSizer.Add(self.buttonSizer, 0, wx.ALL, 0)

		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
		self.Bind(wx.EVT_TEXT_ENTER, self.onOK)

		self.SetSizerAndFit(self.mainSizer)
		self.result = None

	def onOK(self, event):
		self.result = self.field.GetValue()
		self.Destroy()

	def onCancel(self, event):
		self.result = None
		self.Destroy()




def getHwAddr():
	return get_mac()

class Form(wx.Frame):
	def __init__(self, parent):


		self.payment_receipt_image = None
		self.form_data = dict()
		self.form_data = dict()
                
		w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
                h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
                #wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX
                wx.Frame.__init__(self, parent, 1, size=(400,500), pos=(w/2, h/3), style=wx.DEFAULT|wx.STAY_ON_TOP|wx.FRAME_FLOAT_ON_PARENT)

                self.pnl = wx.Panel(self)

                topsizer = wx.BoxSizer(wx.VERTICAL)


                gridSizer = wx.GridSizer(rows=6, cols=2, hgap=5, vgap=8)
                titleSizer = wx.BoxSizer(wx.HORIZONTAL)


                title = wx.StaticText(self, label="""This is the user form to be filled to register to play Modules selected, 
                Please ensure to fill the module and email id correctly""",)
                titleSizer.Add(title, 1, wx.ALL, 5)



                gridSizer.Add(wx.StaticText(self.pnl, label='First Name'), wx.ALIGN_RIGHT)
                gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="first_name"), 0, wx.EXPAND)


                gridSizer.Add(wx.StaticText(self.pnl, label='Last Name'), wx.ALIGN_RIGHT)
                gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="second_name"), 0, wx.EXPAND)

                gridSizer.Add(wx.StaticText(self.pnl, label='Email Id'), wx.ALIGN_RIGHT)
                gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="email_id"), 0, wx.EXPAND)


                gridSizer.Add(wx.StaticText(self.pnl, label='Country'), wx.ALIGN_RIGHT)
                gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="country"), 0, wx.EXPAND)


		choose_button = wx.Button(self.pnl, label='Payment jpeg', id=wx.ID_ANY) 
		self.Bind(wx.EVT_BUTTON,  self.OnOpen, id=choose_button.GetId())
		gridSizer.Add(choose_button, wx.ALIGN_RIGHT)
		self.control=wx.TextCtrl(self.pnl, size= (200, 30), name="jpeg image")
		gridSizer.Add(self.control, 0, wx.EXPAND)




                courses = ["English", "Economics", "Accounts", "Geography", "Business Studies", "Life Sciences"]
                gridSizer.Add(wx.StaticText(self.pnl, label='Modules'), wx.ALIGN_RIGHT)
                gridSizer.Add(wx.ComboBox(self.pnl, size= (200, 30), choices=courses, name="modules", style= wx.CB_DROPDOWN|wx.CB_READONLY),0, wx.EXPAND)



                self.pnl.SetSizer(gridSizer)

                button_box = wx.BoxSizer(wx.HORIZONTAL)
                submitButton = wx.Button(self, label='Submit', id=wx.ID_ANY)
                self.Bind(wx.EVT_BUTTON,  self.OnSubmit, id=submitButton.GetId())

                closeButton = wx.Button(self, label='Close', id=wx.ID_ANY)
                self.Bind(wx.EVT_BUTTON,  self.OnClose, id=closeButton.GetId())
                button_box.Add(submitButton)
                button_box.Add(closeButton, flag=wx.LEFT, border=5)
                topsizer.Add(titleSizer, 0, wx.CENTER, 5)
                topsizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
                topsizer.Add((10, 20))
                topsizer.Add(self.pnl, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
                topsizer.Add(button_box, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)



                self.SetSizerAndFit(topsizer)

	def OnSubmit(self, event):
		wait = wx.BusyCursor() 
		for child in self.pnl.GetChildren():
			if isinstance(child, wx.TextCtrl): 
				if not bool(child.GetValue()):
					dlg = wx.MessageDialog(self, "%s cannot be left empty"%child.GetName(), "Warning", wx.OK | wx.ICON_WARNING)
					dlg.ShowModal()
					dlg.Destroy()
				if child.GetName() == "jpeg image":
					try:
						open(child.GetValue())
					except Exception:
						dlg = wx.MessageDialog(self, "Please enter a valid file", "Warning", wx.OK | wx.ICON_WARNING)
						dlg.ShowModal()
						dlg.Destroy()
						self.Enable()
						return
					

				self.form_data[child.GetName()] = child.GetValue()
			if isinstance(child, wx.ComboBox): 
				if not bool(child.GetValue()):
					dlg = wx.MessageDialog(self, "%s cannot be left empty"%child.GetName(), "Warning", wx.OK | wx.ICON_WARNING)
					dlg.ShowModal()
					dlg.Destroy()
					return


				combobox_value = "".join(child.GetValue().split(" "))
				self.form_data[child.GetName()] = combobox_value
				
		self.form_data["platform"] = sys.platform
		self.form_data["mac_id"] = getHwAddr()
		
		
	
		self.form_data["payment_receipt_image"] = self.payment_receipt_image
		
		try:
			response = requests.post("%s/v1/register_user"%url, data=self.form_data)
			messege = response.json().get("messege")
		except requests.ConnectionError:
			messege = "some how the request cannot be completed, Please check your internet connection"

		dlg = wx.MessageDialog(self, messege, "Notification", wx.OK | wx.ICON_WARNING)
		if dlg.ShowModal() == wx.ID_OK:
			dlg.ShowModal()
			dlg.Destroy()
			self.Destroy()
		del wait
		return

        def OnClose(self, e):
        	self.Destroy()
        

	def OnOpen(self,e):
		""" Open a file"""
		self.dirname = ''
		dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			self.filename = dlg.GetFilename()
			self.dirname = dlg.GetDirectory()
			try:
				f = open(os.path.join(self.dirname, self.filename), 'rb')
				self.control.SetValue(os.path.join(self.dirname, self.filename))
				self.payment_receipt_image = base64.encodestring(f.read())
				f.close()

			except IOError as e:
				dlg = wx.MessageDialog(self, "Please enetr a valid file", "Warning", wx.OK | wx.ICON_WARNING)
				dlg.ShowModal()
				dlg.Destroy()
				return
		dlg.Destroy()


#This list has all the colors available in wx python


class CanvasPanel(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, -1, size=(510,300), pos=((wx.DisplaySize()[0])/2,(wx.DisplaySize()[1])/2), style=wx.CLOSE_BOX)

		self.hbox = wx.BoxSizer(wx.VERTICAL)
		self.panel = wx.Panel(self, 3, style=wx.RAISED_BORDER)

		font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
		font.SetPointSize(8)
		text = """    Welcome to METC E Learning Courses.
		
				If you have authorization code, prese yes
				or press no to register .
		"""   

		self.text = wx.StaticText(self.panel, label=text)
		self.text.SetFont(font)

		self.button_box = wx.BoxSizer(wx.HORIZONTAL)
		self.button_panel = wx.Panel(self, 1, style=wx.RAISED_BORDER)
		self.button_one = wx.Button(self.button_panel, ID_ONE, label='Yes', size=(160, 30))
		self.button_two = wx.Button(self.button_panel, ID_TWO, label='No', size=(160, 30))
		self.button_three = wx.Button(self.button_panel, ID_THREE, label='Close', size=(160, 30))

		self.Bind(wx.EVT_BUTTON, self.yes_authentication_code, id=ID_ONE)
		self.Bind(wx.EVT_BUTTON, self.no_authentication_code, id=ID_TWO)
		self.Bind(wx.EVT_BUTTON, self.close_window, id=ID_THREE)

		self.button_box.Add(self.button_one, wx.ALIGN_LEFT|wx.EXPAND)
		self.button_box.Add(self.button_two, wx.ALIGN_CENTER|wx.EXPAND)
		self.button_box.Add(self.button_three, wx.ALIGN_RIGHT|wx.EXPAND)

		self.button_panel.SetSizer(self.button_box)
		self.hbox.Add(self.panel, 2, wx.EXPAND | wx.ALL, 3)
		self.hbox.Add(self.button_panel, 1, wx.EXPAND | wx.ALL, 3)
		self.SetSizerAndFit(self.hbox)
		self.SetBackgroundColour("light blue")
		self.Centre()
		self.Show()


	def no_authentication_code(self, event):
		self.Enable(False)
		dia = Form(self)
		dia.Show(True)	
		self.Enable(True)
		return

	def close_window(self, event):
		self.Close()
	

	def disable_buttons(self, flag):
		for button in self.button_panel.GetChildren():
			if not flag:
				button.Enable()
			else:
				button.Disable()

	def yes_authentication_code(self, event):
		#frame = wx.TextEntryDialog(self, "Enter the authentication code", "", style=wx.OK|wx.CANCEL)
		frame = Authentication(self)
		frame.ShowModal()
		mac_id = getHwAddr()
		
		if not frame.result:
			return

		response = requests.get("%s/v1/download?mac_id=%s&key=%s&path=%s&check_module=%s"%(url, mac_id, frame.result, False, True))
			
		
		if response.json().get("error"):
			dlg = wx.MessageDialog(self, response.json().get("messege"), "Warning", wx.OK | wx.ICON_WARNING)
			dlg.ShowModal()
			dlg.Destroy()
			return
		
		module_name = response.json()["module_name"]
		hashkey = response.json()["hash"]
		user_os = sys.platform[:3]
		working_dir = os.path.abspath(os.path.dirname("__file__"))
		#This creates a new working directory with parent directory in which this .exe is running by the name of the data
		
		
		path = "%s/%s_%s.zip"%(working_dir, user_os[:3], module_name)

		print path
		try:
				
			#SEcond time user
			if os.path.exists(path):
				self.already_registered_user(response, path, hashkey, module_name, user_os)
		
			else:
				self.new_user(response, path, frame.result, module_name, user_os, mac_id)

		except requests.ConnectionError:
			raise StandardError("Your internet connection is not working")	
		
		return


	def already_registered_user(self, response, path, hashkey, module_name, user_os):

		dirpath = tempfile.mkdtemp()
		
		try:
			zip_file = zipfile.ZipFile(path) 
		except :
			dlg = wx.MessageDialog(self, "There was some error while downloading the course file, Please download it again", "Warning", wx.OK | wx.ICON_WARNING)
		
			dlg.ShowModal()
			dlg.Destroy()
			os.unlink(path)
			return 
		

		with  cd(dirpath):
				zip_file = zipfile.ZipFile(path) 
				zipfile.ZipFile.extractall(zip_file, pwd=hashkey)
				
				Run_Unzip("%s_%s.zip"%(user_os[:3], module_name), dirpath, None, "Extracting files....")
				#zip_file = zipfile.ZipFile("%s_%s.zip"%(user_os[:3], module_name))
				#zipfile.ZipFile.extractall(zip_file)
				
				if user_os == "win":
					subprocess.call(["Play me.exe"])
				elif user_os == "lin":
					subprocess.call(["ls"])
					subprocess.call(["wine", "Play me.exe"])
				
				else:
					subprocess.call(["wine", "Play me.exe"])
		
		shutil.rmtree(dirpath)

		return


	def new_user(self, response, path, key, module_name, user_os, mac_id):
		#r = requests.get("%s/v1/download?mac_id=%s&key=%s&path=%s"%(url, mac_id, key, False))

		link = "%s/v1/download?mac_id=%s&key=%s&path=%s"%(url, mac_id, key, False)
		"""
		if r.headers.get("content-length"):
			dlg = wx.MessageDialog(self, r.json().get("messege"), "Warning", wx.OK | wx.ICON_WARNING)
			dlg.ShowModal()
			dlg.Destroy()
			return
		"""

		Run_Download(path, link, "Please wait while the file is being downloaded")
		#zf = zipfile.ZipFile(path, mode='w')
		#zf.fp.write(r.content)
		#zf.fp.close()


		#if path doesnt exists the response will have the zip file and this writes that encrypted zip file into the path
		#Now the Data Folder do have WholeZip.zip and now the path exists

		dirpath = tempfile.mkdtemp()
				
		response = requests.get("%s/v1/download?mac_id=%s&key=%s&path=%s"%(url, mac_id, key, True))
	
		try:
			zip_file = zipfile.ZipFile(path) 
		except :
			dlg = wx.MessageDialog(self, "There was some error while downloading the course file, Please download it again" , "Warning", wx.OK | wx.ICON_WARNING)
			dlg.ShowModal()
			dlg.Destroy()
			os.unlink(path)
			return 
		


		with  cd(dirpath):
				zip_file = zipfile.ZipFile(path) 
				zipfile.ZipFile.extractall(zip_file, pwd=response.json().get("hash"))
				
				
				Run_Unzip("%s_%s.zip"%(user_os[:3], module_name), dirpath, None, "Extracting files....")
				#zip_file = zipfile.ZipFile("%s_%s.zip"%(user_os[:3], module_name)) 
				#zipfile.ZipFile.extractall(zip_file)
				
				if user_os == "win":

					subprocess.call(["Play me.exe"])
				elif user_os == "lin":
					subprocess.call(["ls"])
					subprocess.call(["wine", "Play me.exe"])
				
				else:
					print "user os cannot be determined"
	
		shutil.rmtree(dirpath)
		return




class cd:
	"""Context manager for changing the current working directory"""
	def __init__(self, newPath):
		self.newPath = newPath

	def __enter__(self):
		self.savedPath = os.getcwd()
		os.chdir(self.newPath)

	def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)


def run_app():
	app = wx.App(False)
	app.frame = CanvasPanel()
	
	app.frame.Show(True)
	
	app.frame.Center()
	app.MainLoop()



if __name__ == "__main__":

	run_app()
