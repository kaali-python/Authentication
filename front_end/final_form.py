#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import wx
import requests
import time
url = "http://localhost:8989/v1"

class Form(wx.Frame):
	def __init__(self):
		self.form_data = dict()
		w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
		h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
		#wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX
           	wx.Frame.__init__(self, None, 1, size=(400,500), pos=(w/2, h/3), style=wx.DEFAULT)          
		
		self.pnl = wx.Panel(self)

		topsizer = wx.BoxSizer(wx.VERTICAL)


		gridSizer = wx.GridSizer(rows=6, cols=2, hgap=5, vgap=8)
		titleSizer = wx.BoxSizer(wx.HORIZONTAL)	
	

		title = wx.StaticText(self, label="""This is the user form to be filled to register to play Modules selected, 
		Please ensure to fill the module and email id correctly""",)
		titleSizer.Add(title, 0, wx.ALL, 5)
		
        

		gridSizer.Add(wx.StaticText(self.pnl, label='First Name'), wx.ALIGN_RIGHT)
		gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="first_name"), 0, wx.EXPAND)


		gridSizer.Add(wx.StaticText(self.pnl, label='Last Name'), wx.ALIGN_RIGHT)
		gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="second_name"), 0, wx.EXPAND)
		
		gridSizer.Add(wx.StaticText(self.pnl, label='Email Id'), wx.ALIGN_RIGHT)
		gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="email_id"), 0, wx.EXPAND)
		
		gridSizer.Add(wx.StaticText(self.pnl, label='Country'), wx.ALIGN_RIGHT)
		gridSizer.Add(wx.TextCtrl(self.pnl, size= (200, 30), name="country"), 0, wx.EXPAND)
		

		courses = ["Accounting", "Economics", "Finance", "Philosophy"]
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
		print "Onsubmit has been clicked"
		for child in self.pnl.GetChildren():
			if isinstance(child, wx.TextCtrl): 
				if not bool(child.GetValue()):
					dlg = wx.MessageDialog(self, "%s cannot be left empty"%child.GetName(), "Warning", wx.OK | wx.ICON_WARNING)
					dlg.ShowModal()
					dlg.Destroy()
					return

				self.form_data[child.GetName()] = child.GetValue()
			if isinstance(child, wx.ComboBox): 
				if not bool(child.GetValue()):
					dlg = wx.MessageDialog(self, "%s cannot be left empty"%child.GetName(), "Warning", wx.OK | wx.ICON_WARNING)
					dlg.ShowModal()
					dlg.Destroy()
					return
				self.form_data[child.GetName()] = child.GetValue()
		
		self.form_data["platform"] = sys.platform
		self.form_data["mac_id"] = getHwAddr("eth0")

		response = requests.post("%s/register_user"%url, data=self.form_data)
		dlg = wx.MessageDialog(self, response.json().get("messege"), "Notification", wx.OK | wx.ICON_WARNING)
		dlg.ShowModal()
		dlg.Destroy()
		print response.text
		print self.form_data
		
		
		self.Destroy()
		return

        def OnClose(self, e):
        	self.Destroy()
        
def run_app():
        app = wx.App(False)
        app.frame = Form()
        app.frame.Show(True)
        app.frame.Center()
        app.MainLoop()



if __name__ == "__main__":

        run_app()


