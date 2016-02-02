import json, re, time, argparse, signal, os
import tkinter as tk
from opcserver import *

class MainWindow(tk.Frame):

	# ------------------------------------------------------
	def __init__(self, parent=None):
		self.parent = parent
		self.win_width = 800
		self.win_height = 600
		self.led_widgets = []
		self.led_rects = []
		self.parseCmdArgs()

		tk.Frame.__init__(self, parent)
		self.pack()
		self.readConfig(self.layout_file ,self.layout_type)
		self.opcServer = OPCserver(self.updateLeds)
		self.opcServer.start()

		self.initUI()

		for idx in range(len(self.led_widgets)):
			self.setLedColor(idx,100,200,100)

	# ------------------------------------------------------
	def initUI(self):
		self.canvas = tk.Canvas(self, width=self.win_width, height=self.win_height)
		self.canvas.pack()
		self.canvas.create_rectangle(0, 0, self.win_width, self.win_height, fill="darkgray", outline="darkgray")

		for r in self.led_rects:
			self.led_widgets.append(self.canvas.create_rectangle(r[0], r[1], r[2], r[3], fill="black", outline="darkgray"))
			if self.show_numbers:
				self.canvas.create_text( int((r[0]+r[2])/2), int((r[1]+r[3])/2), anchor=tk.W, text=str(idx))

	# ------------------------------------------------------
	def parseCmdArgs(self):
		parser = argparse.ArgumentParser(description='Simulator for hyperion.', prog='hypersim')
		parser.add_argument('--num', dest='show_numbers', action='store_const', const=True, default=False, help='show led IDs')
		parser.add_argument('--hyperion', default=None, help='hyperion config')
		parser.add_argument('--opc_xy', default=None, help='opc config xy components')
		parser.add_argument('--opc_yz', default=None, help='opc config yz components')
		parser.add_argument('--opc_xz', default=None, help='opc config xz components')

		args = parser.parse_args()
		self.show_numbers = args.show_numbers
		if args.hyperion is None and args.opc_xy is None  and args.opc_yz is None and args.opc_xz is None:
			print("missing configuration file")
			exit(1)
		
		if args.hyperion is not None:
			self.layout_file = args.hyperion
			self.layout_type = "hyperion"
			if not os.path.exists(self.layout_file):
				print("could not read ", self.layout_file)
				exit(1)

		elif args.opc_xy is not None:
			self.layout_file = args.opc_xy
			self.layout_type = "opc_xy"
			if not os.path.exists(self.layout_file):
				print("could not read ", self.layout_file)
				exit(1)

		elif args.opc_xz is not None:
			self.layout_file = args.opc_xz
			self.layout_type = "opc_xz"
			if not os.path.exists(self.layout_file):
				print("could not read ", self.layout_file)
				exit(1)

		elif args.opc_yz is not None:
			self.layout_file = args.opc_yz
			self.layout_type = "opc_yz"
			if not os.path.exists(self.layout_file):
				print("could not read ", self.layout_file)
				exit(1)

	# ------------------------------------------------------
	def on_close(self):
		self.opcServer.stop()
		#self.opcServer.join()
		self.parent.destroy()
		exit(0)

	# ------------------------------------------------------
	def readConfig_hyperion(self,layout_file):
		with open(layout_file) as data_file:
			data = ""
			cfg_data = data_file.read()
			for line in cfg_data.splitlines():
				data += line.split('//')[0]
			hyperion_cfg = json.loads(data)

			for led in hyperion_cfg['leds']:
				self.led_rects.append([
					int(led['hscan']['minimum'] * self.win_width), 
					int(led['vscan']['minimum'] * self.win_height),
					int(led['hscan']['maximum'] * self.win_width), 
					int(led['vscan']['maximum'] * self.win_height)
				])

	# ------------------------------------------------------
	def readConfig_opc(self,layout_file,a_val_idx,b_val_idx):
		a_values = []
		b_values = []
		with open(layout_file) as data_file:
			opc_cfg = json.load(data_file)
			#print(opc_cfg)
			for d in opc_cfg:
				a_values.append(d['point'][a_val_idx])
				b_values.append(d['point'][b_val_idx])

			a_values_max = max(a_values)
			a_values_min = min(a_values)
			b_values_max = max(b_values)
			b_values_min = min(b_values)

			# calc ratio
			#print( abs(b_values_max - b_values_min) / abs(a_values_max - a_values_min),  a_values_max - a_values_min )
			
			self.win_height = 800
			while True:
				self.win_height = self.win_width * (abs(b_values_max - b_values_min) / abs(a_values_max - a_values_min))
				if self.win_height < 800:
					break
				else:
					self.win_width -= 10

			norm_a = lambda x: (x - a_values_min) / (a_values_max - a_values_min);
			norm_b = lambda x: (x - b_values_min) / (b_values_max - b_values_min);
			
			for idx in range(len(a_values)):
				self.led_rects.append([
					int(norm_a(a_values[idx]) * (self.win_width-30)+5), 
					int(norm_a(b_values[idx]) * (self.win_height-30)+5),
					int(norm_a(a_values[idx]) * (self.win_width-30)+20), 
					int(norm_a(b_values[idx]) * (self.win_height-30)+20)
				])

	# ------------------------------------------------------
	def readConfig(self,layout_file, layout_type="hyperion"):
			if layout_type == "hyperion":
				self.readConfig_hyperion(layout_file)
			elif layout_type == "opc_xy":
				self.readConfig_opc(layout_file,0,1)
			elif layout_type == "opc_yz":
				self.readConfig_opc(layout_file,1,2)
			elif layout_type == "opc_xz":
				self.readConfig_opc(layout_file,0,2)
			else:
				print("unknown type of config file")
				exit(1)

	# ------------------------------------------------------
	def updateLeds(self, led_data):
		for idx in range(len(led_data)):
			self.setLedColor(idx,led_data[idx][0],led_data[idx][1],led_data[idx][2])
		
	# ------------------------------------------------------
	def setLedColor(self,led_idx,r,g,b):
		if led_idx < len(self.led_widgets):
			self.canvas.itemconfigure(self.led_widgets[led_idx], fill="#%02x%02x%02x" % (r, g, b) )

