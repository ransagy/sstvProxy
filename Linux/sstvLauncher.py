import os, subprocess, sys, urllib, json, logging, ntpath, platform, requests, shutil, threading, multiprocessing, signal
from logging.handlers import RotatingFileHandler

import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator


def create_menu_item(menu, label, func):
	item = wx.MenuItem(menu, -1, label)
	menu.Bind(wx.EVT_MENU, func, id=item.GetId())
	menu.Append(item)
	return item

# Setup logging
log_formatter = logging.Formatter(
	'%(asctime)s - %(levelname)-10s - %(name)-10s -  %(funcName)-25s- %(message)s')

logger = logging.getLogger('SmoothStreamsLauncher ')
logger.setLevel(logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Console logging
console_handler = logging.StreamHandler()

console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Rotating Log Files
if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), 'cache')):
	os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), 'cache'))
file_handler = RotatingFileHandler(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'status.log'),
								   maxBytes=1024 * 1024 * 2,
								   backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)


# class system_tray(object):
class TaskBarIcon(object):
	def __init__(self):

		self.type = ""
		self.version = float("0.0")
		self.latestVersion = float("0.0")
		# Branch Master = True
		self.branch = True
		self.yap = None
		self.LISTEN_IP = '127.0.0.1'
		self.LISTEN_PORT = 6969
		self.SERVER_HOST = "http://" + self.LISTEN_IP + ":" + str(self.LISTEN_PORT)
		start = False
		try:
			logger.debug("Parsing settings")
			with open(os.path.join(os.path.dirname(sys.argv[0]), 'launcher.json')) as jsonConfig:
				config = {}
				config = json.load(jsonConfig)
				if "version" in config:
					self.version = config["version"]
				if "type" in config:
					self.type = config["type"]
				if "branch" in config:
					self.branch = config["branch"] == True
				self.assign_latestFile()
				self.check_install()
				start = True
		except:
			urllib.request.urlretrieve('https://raw.githubusercontent.com/vorghahn/sstvProxy/master/logo_tray.ico', os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray.ico'))
			urllib.request.urlretrieve('https://raw.githubusercontent.com/vorghahn/sstvProxy/master/logo_tray-update.ico', os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray-update.ico'))
			self.detect_install()
			self.assign_latestFile()
		self.version = float(self.version)

		logger.info(u"Launching system tray icon.")
		self.ind = appindicator.Indicator.new (
				        "sstvLauncherTray",
				         os.path.abspath('logo_tray.ico'),
				        appindicator.IndicatorCategory.APPLICATION_STATUS)
		self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
		self.ind.set_attention_icon ("indicator-messages-new")

		# create a menu
		menu = Gtk.Menu()

		# this is where you would connect your menu item up with a function:

		menu_items = Gtk.MenuItem('Open YAP')
		menu_items.connect("activate", self.tray_open)
		menu.append(menu_items)

		#menu.AppendSeparator()
		menu_items = Gtk.MenuItem('Check for Updates')
		menu_items.connect("activate", self.tray_check_update)
		menu.append(menu_items)

		menu_items = Gtk.MenuItem('Update')
		menu_items.connect("activate", self.tray_update)
		menu.append(menu_items)

		menu_items = Gtk.MenuItem('Start/Restart YAP')
		menu_items.connect("activate", self.tray_restart)
		menu.append(menu_items)

		menu_items = Gtk.MenuItem('Switch Master/Dev')
		menu_items.connect("activate", self.tray_branch)
		menu.append(menu_items)

		menu_items = Gtk.MenuItem('Open Logs')
		menu_items.connect("activate", self.tray_logs)
		menu.append(menu_items)

		menu_items = Gtk.MenuItem('Clear Cache')
		menu_items.connect("activate", self.tray_cache)
		menu.append(menu_items)

		menu_items = Gtk.MenuItem('Exit')
		menu_items.connect("activate", self.on_exit)
		menu.append(menu_items)

		# show the items
		menu.show_all()

		self.ind.set_menu(menu)
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		if start:
			self.tray_start()

		self.set_icon()
		Gtk.main()

		



	def gather_yap(self):
		if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettings.json')):
			logger.debug("No config file found.")
		try:
			logger.debug("Parsing settings")
			with open(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettings.json')) as jsonConfig:
				config = {}
				config = json.load(jsonConfig)
				if "ip" in config and "port" in config:
					self.LISTEN_IP = config["ip"]
					self.LISTEN_PORT = config["port"]
					self.SERVER_HOST = "http://" + self.LISTEN_IP + ":" + str(self.LISTEN_PORT)
				logger.debug("Using config file.")
		except:
			pass

	def tray_update(self, w):
		if self.version < self.latestVersion:
			# todo make update link
			self.shutdown(update=True)
			self.set_icon()
		else:
			icon = os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray.ico')
			#icon = wx.Icon(icon)
			hover_text = 'YAP' + ' - No Update Available'
			self.set_icon()
			
	def CreatePopupMenu(self):
		menu = wx.Menu()
		create_menu_item(menu, 'Open YAP', self.tray_open)
		menu.AppendSeparator()
		create_menu_item(menu, 'Check for Updates', self.tray_check_update)
		create_menu_item(menu, 'Update', self.tray_update)
		create_menu_item(menu, 'Start/Restart YAP', self.tray_restart)
		create_menu_item(menu, 'Switch Master/Dev', self.tray_branch)
		create_menu_item(menu, 'Open Logs', self.tray_logs)
		create_menu_item(menu, 'Clear Cache', self.tray_cache)
		create_menu_item(menu, 'Exit', self.on_exit)
		return menu

	def set_icon(self):
		if self.version < self.latestVersion:
			icon = os.path.abspath('logo_tray-update.ico')
			hover_text = 'YAP' + ' - Update Available!'

		else:
			icon = os.path.abspath('logo_tray.ico')
			hover_text = 'YAP'
		self.ind.set_icon(icon)
		#icon = wx.Icon(icon)
		#self.SetIcon(icon, hover_text)

	def on_exit(self, w):
		if self.yap: self.yap.terminate()
		Gtk.main_quit()
		#wx.CallAfter(self.Destroy)
		#self.frame.Close()

	def detect_install(self):
		logger.info("Detect install")
		if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvProxy.py')):
			logger.info("Detect python")
			self.type = ""
			return
		elif platform.system() == 'Linux':
			if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvProxy')):
				logger.info("Detect linux exe")
				self.type = "Linux/"
				return
		elif platform.system() == 'Windows':
			if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvproxy.exe')):
				logger.info("Detect win exe")
				self.type = "Windows/"
				return
		elif platform.system() == 'Darwin':
			if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvproxy')):
				logger.info("Detect mac exe")
				self.type = "Macintosh/"
				return
		logger.info('installing')
		self.type = "Windows/"
		self.assign_latestFile()
		self.shutdown(update=True)


	def check_install(self):
		logger.info("Check install")
		if self.type == "" and os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvProxy.py')):
			return
		elif self.type == "Linux/" and platform.system() == 'Linux' and os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvProxy')):
			return
		elif self.type == "Windows/" and platform.system() == 'Windows'and os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvproxy.exe')):
			return
		elif self.type == "Macintosh/" and platform.system() == 'Darwin' and os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvproxy')):
			return
		logger.info('Installing YAP %s' % self.type)
		self.assign_latestFile()
		self.shutdown(update=True)


	def assign_latestFile(self):
		if self.type == "": self.latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/{branch}/sstvProxy.py"
		elif self.type == "Linux/": self.latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/{branch}/Linux/sstvProxy"
		elif self.type == "Windows/": self.latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/{branch}/Windows/sstvproxy.exe"
		elif self.type == "Macintosh/": self.latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/{branch}/Macintosh/sstvproxy"
		self.url = "https://raw.githubusercontent.com/vorghahn/sstvProxy/master/%sversion.txt" % self.type
		try:
			self.latestVersion = float(requests.get(self.url).json()['Version'])
		except:
			self.latestVersion = float(0.0)
			logger.info("Latest version check failed, check internet.")

	def tray_open(self, w):
		self.launch_browser()

	def tray_check_update(self, w):
		try:
			latest_ver = float(json.loads(urllib.request.urlopen(self.url).read().decode('utf-8'))['Version'])
		except:
			latest_ver = float(0.0)
			logger.info("Latest version check failed, check internet.")
		if self.version < latest_ver:
			logger.info("Update Available. You are on v%s with v%s available." % (self.version, latest_ver))
		else:
			logger.info("Proxy is up to date!")

	def save_data(self):
		config = {'version':self.version,'type':self.type,'branch':self.branch}
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'launcher.json'), 'w') as fp:
			json.dump(config, fp)

	def tray_start(self):
		if self.type == "":
			import sstvProxy
			self.yap = multiprocessing.Process (target=sstvProxy.main)
			self.yap.start()

		elif self.type == "Linux/": os.execv(sys.executable, ["./sstvProxy", "-d"]) #subprocess.call(["./sstvProxy", "-d"])
		elif self.type == "Windows/": subprocess.Popen([".\sstvproxy.exe", "-d"], cwd=os.getcwd()) #subprocess.call([".\sstvproxy.exe", "-d"])
		elif self.type == "Macintosh/": os.execv(sys.executable, ["./sstvproxy", "-d"])

	def tray_restart(self, w):
		self.shutdown(restart=True)

	def tray_quit(self, w):
		self.shutdown()

	def tray_cache(self, w):
		shutil.rmtree(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), ignore_errors=True)

	def tray_logs(self, w):
		try:
			import webbrowser
			webbrowser.open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'status.log'))
		except Exception as e:
			logger.error(u"Could not open logs: %s" % e)

	def tray_branch(self, w):
		self.branch = not self.branch
		self.shutdown(update=True, restart=True)
		#self.set_icon()

	def launch_browser(self):
		try:
			import webbrowser
			self.gather_yap()
			webbrowser.open('%s%s' % (self.SERVER_HOST,'/sstv/index.html'))
		except Exception as e:
			logger.error(u"Could not launch browser: %s" % e)

	def shutdown(self, restart=False, update=False, checkout=False, closeLauncher=False):
		logger.info(u"Stopping YAP web server...")
		if self.type == 'Windows/':
			os.system("taskkill /F /im sstvProxy.exe")
		elif self.type == 'Linux/':
			import psutil
			PROCNAME = "sstvProxy"
			for proc in psutil.process_iter():
				# check whether the process name matches
				if proc.name() == PROCNAME:
					proc.kill()
		elif self.type == 'Macintosh/':
			import psutil
			PROCNAME = "sstvproxy"
			for proc in psutil.process_iter():
				# check whether the process name matches
				if proc.name() == PROCNAME:
					proc.kill()
		elif self.yap:
			self.yap.terminate()
			self.yap = None

		if not restart and not update and not checkout:
			logger.info(u"YAP is shutting down...")

		if update:
			logger.info(u"YAP is updating...")
			url = self.latestfile.format(branch='master' if self.branch else 'dev')
			try:
				newfilename = ntpath.basename(url)
				logger.debug("downloading %s to %s" % (url,os.path.join(os.path.dirname(sys.argv[0]), newfilename)))

				urllib.request.urlretrieve(url, os.path.join(os.path.dirname(sys.argv[0]), newfilename))
			except Exception as e:
				os.system("taskkill /F /im sstvProxy.exe")
				urllib.request.urlretrieve(url, os.path.join(os.path.dirname(sys.argv[0]), newfilename))
				logger.info("Update forced")
			self.version = float(json.loads(urllib.request.urlopen(self.url).read().decode('utf-8'))['Version'])
			self.save_data()



		if checkout:
			pass

		if restart:
			os.system('cls' if os.name == 'nt' else 'clear')
			logger.info(u"YAP is restarting...")
			self.tray_start()
			# exe = sys.executable
			# args = [exe, sys.argv[0]]
			# args += sys.argv[1:]
			# # if '--nolaunch' not in args:
			# # 	args += ['--nolaunch']
			#
			# # Separate out logger so we can shutdown logger after
			# if NOFORK:
			# 	logger.info('Running as service, not forking. Exiting...')
			# elif os.name == 'nt':
			# 	logger.info('Restarting YAP with %s', args)
			# else:
			# 	logger.info('Restarting YAP with %s', args)
			#
			# # logger.shutdown()
			#
			# # os.execv fails with spaced names on Windows
			# # https://bugs.python.org/issue19066
			# if NOFORK:
			# 	pass
			# elif os.name == 'nt':
			# 	subprocess.Popen(args, cwd=os.getcwd())
			# else:
			# 	os.execv(exe, args)


		if closeLauncher:
			os._exit(0)

#class App(wx.App):
	#def OnInit(self):
		#frame=wx.Frame(None)
		#self.SetTopWindow(frame)
		#TaskBarIcon(frame)
		#return True

#def main():
	#app = App(False)
	#app.MainLoop()

if __name__ == '__main__':
	#main()
	TaskBarIcon()
