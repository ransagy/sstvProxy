import os, subprocess, sys, urllib, json, logging, ntpath, platform, requests, shutil
from logging.handlers import RotatingFileHandler
import wx.adv
import wx
TRAY_TOOLTIP = 'Name'
TRAY_ICON = 'icon.png'


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
class TaskBarIcon(wx.adv.TaskBarIcon):
	def __init__(self, frame):
		self.frame = frame
		super(TaskBarIcon, self).__init__()
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.tray_open)
		self.type = ""
		self.version = float("0.0")
		self.latestVersion = None
		# Branch Master = True
		self.branch = True
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
					self.branch = config["branch"] == "True"
				self.assign_latestFile()
				self.check_install()
				start = True
		except:
			self.detect_install()
		self.version = float(self.version)

		logger.info(u"Launching system tray icon.")
		self.set_icon()

		if start:
			self.tray_start()

			
	def tray_update(self, sysTrayIcon):
		if self.version < self.latestVersion:
			# todo make update link
			self.shutdown(update=True)
			self.set_icon()
		else:
			icon = os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray.ico')
			icon = wx.Icon(icon)
			hover_text = 'YAP' + ' - No Update Available'
			self.SetIcon(icon, hover_text)
			
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
			icon = os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray-update.ico')
			hover_text = 'YAP' + ' - Update Available!'

		else:
			icon = os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray.ico')
			hover_text = 'YAP'
		icon = wx.Icon(icon)
		self.SetIcon(icon, hover_text)

	def on_exit(self, event):
		wx.CallAfter(self.Destroy)
		self.frame.Close()

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
		self.version = float(json.loads(urllib.request.urlopen(self.url).read().decode('utf-8'))['Version'])
		self.save_data()

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
		self.version = float(json.loads(urllib.request.urlopen(self.url).read().decode('utf-8'))['Version'])
		self.save_data()

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

	def tray_open(self, sysTrayIcon):
		self.launch_browser()

	def tray_check_update(self, sysTrayIcon):
		try:
			latest_ver = float(json.loads(urllib.request.urlopen(self.url).read().decode('utf-8'))['Version'])
		except:
			latest_ver = float(0.0)
			logger.info("Latest version check failed, check internet.")
		if self.version < latest_ver:
			logger.info("Update Available")
		else:
			logger.info("Proxy is up to date!")

	def save_data(self):
		config = {'version':self.version,'type':self.type,'branch':self.branch}
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'launcher.json'), 'w') as fp:
			json.dump(config, fp)

	def tray_start(self):
		if self.type == "":
			import sstvProxy
			sstvProxy.main()
		elif self.type == "Linux/": os.execv(sys.executable, ["./sstvProxy", "-d"]) #subprocess.call(["./sstvProxy", "-d"])
		elif self.type == "Windows/": subprocess.Popen([".\sstvproxy.exe", "-d"], cwd=os.getcwd()) #subprocess.call([".\sstvproxy.exe", "-d"])
		elif self.type == "Macintosh/": os.execv(sys.executable, ["./sstvproxy", "-d"])

	def tray_restart(self, sysTrayIcon):
		self.shutdown(restart=True)

	def tray_quit(self, sysTrayIcon):
		self.shutdown()

	def tray_cache(self, sysTrayIcon):
		shutil.rmtree(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), ignore_errors=True)

	def tray_logs(self, sysTrayIcon):
		try:
			import webbrowser
			webbrowser.open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'status.log'))
		except Exception as e:
			logger.error(u"Could not open logs: %s" % e)

	def tray_branch(self, sysTrayIcon):
		self.branch = not self.branch
		self.shutdown(update=True, restart=True)
		self.set_icon()

	def launch_browser(self):
		LISTEN_IP = '127.0.0.1'
		LISTEN_PORT = 100
		try:
			import webbrowser
			webbrowser.open('%s://%s:%i%s' % ('http', LISTEN_IP, LISTEN_PORT, '/sstv/index.html'))
		except Exception as e:
			logger.error(u"Could not launch browser: %s" % e)

	def shutdown(self, restart=False, update=False, checkout=False, closeLauncher=False):
		logger.info(u"Stopping YAP web server...")
		if self.type == '/Windows':
			os.system("taskkill /F /im sstvProxy.exe")

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

class App(wx.App):
	def OnInit(self):
		frame=wx.Frame(None)
		self.SetTopWindow(frame)
		TaskBarIcon(frame)
		return True

def main():
	app = App(False)
	app.MainLoop()

if __name__ == '__main__':
	main()