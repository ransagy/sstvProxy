import sys, signal, os, urllib, subprocess, json, logging, ntpath, platform, requests, shutil, threading, multiprocessing
from PyQt4 import QtGui, QtCore
if platform.system() == 'Linux': print("To run without terminal launch using 'nohup ./sstvLauncher &'")

from logging.handlers import RotatingFileHandler

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



class SystemTrayIcon(QtGui.QSystemTrayIcon):
	def __init__(self, icon, parent=None):
		self.initVariables()
		QtGui.QSystemTrayIcon.__init__(self,icon,parent)
		self.menu = QtGui.QMenu(parent)

		self.createMenu()
		self.setContextMenu(self.menu)

		self.set_icon()

		if self.start:
			logger.info("Launching YAP!")

			self.tray_start()
		else:
			logger.info("not launching")

	def createMenu(self,update=False):
		if update: self.menu.clear()

		if self.start:
			openAction = self.menu.addAction('Open YAP')
			QtCore.QObject.connect(openAction, QtCore.SIGNAL('triggered()'), self.tray_open)

			terminalAction = self.menu.addAction('Show Terminal')
			QtCore.QObject.connect(terminalAction, QtCore.SIGNAL('triggered()'), self.showTerminal)
		else:
			startAction = self.menu.addAction('Start YAP')
			QtCore.QObject.connect(startAction, QtCore.SIGNAL('triggered()'), self.tray_restart)

		self.menu.addSeparator()
		checkAction = self.menu.addAction('Check for Updates')
		QtCore.QObject.connect(checkAction, QtCore.SIGNAL('triggered()'), self.tray_check_update)

		updateAction = self.menu.addAction('Update')
		QtCore.QObject.connect(updateAction, QtCore.SIGNAL('triggered()'), self.tray_update)

		if self.start:
			restartAction = self.menu.addAction('Restart YAP')
			QtCore.QObject.connect(restartAction, QtCore.SIGNAL('triggered()'), self.tray_restart)

		branchAction = self.menu.addAction('Switch Master/Dev')
		QtCore.QObject.connect(branchAction, QtCore.SIGNAL('triggered()'), self.tray_branch)

		logAction = self.menu.addAction('Open Logs')
		QtCore.QObject.connect(logAction, QtCore.SIGNAL('triggered()'), self.tray_logs)

		cacheAction = self.menu.addAction('Clear Cache')
		QtCore.QObject.connect(cacheAction, QtCore.SIGNAL('triggered()'), self.tray_cache)

		exitAction = self.menu.addAction('Exit')
		QtCore.QObject.connect(exitAction, QtCore.SIGNAL('triggered()'), self.on_exit)


	def initVariables(self):
		self.type = ""
		self.version = float("0.0")
		self.latestVersion = float("0.0")
		# Branch Master = True
		self.branch = True
		self.yap = None
		self.LISTEN_IP = '127.0.0.1'
		self.LISTEN_PORT = 6969
		self.SERVER_HOST = "http://" + self.LISTEN_IP + ":" + str(self.LISTEN_PORT)
		self.start = False
		self.validIcon = QtGui.QIcon("logo_tray.ico")
		self.updateIcon = QtGui.QIcon("logo_tray-update.ico")
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
				self.start = True
		except:
			urllib.request.urlretrieve('https://raw.githubusercontent.com/vorghahn/sstvProxy/master/logo_tray.ico',
			                           os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray.ico'))
			urllib.request.urlretrieve(
				'https://raw.githubusercontent.com/vorghahn/sstvProxy/master/logo_tray-update.ico',
				os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray-update.ico'))
			self.detect_install()
			self.assign_latestFile()
		self.version = float(self.version)
		logger.debug("Settings complete")
		return

	def closeEvent(self, event):
		if self.okayToClose(): 
			#user asked for exit
			self.trayIcon.hide()
			event.accept()
		else:
			#"minimize"
			self.hide()
			self.trayIcon.show() #thanks @mojo
			event.ignore()

	def __icon_activated(self, reason):
		if reason in (QtGui.QSystemTrayIcon.Trigger, QtGui.QSystemTrayIcon.DoubleClick):
			logger.info("double clicked")
			self.show()

	def on_exit(self):
		if self.yap: self.yap.terminate()
		self.exit()

	def exit(self):
		QtCore.QCoreApplication.exit()

	def showTerminal(self):
		import time		
		import select
		if platform.system() == 'Linux':
			#subprocess.Popen(args, stdout=subprocess.PIPE)
			try:
				subprocess.Popen(["gnome-terminal -e 'bash -c \"tail -F ./nohup.out; exec bash\"'"], shell=True)
			except:
				subprocess.Popen(["lxterminal -e 'bash -c \"tail -F ./nohup.out; exec bash\"'"], shell=True)
			return
			f = subprocess.Popen(['tail','-F','nohup.out'], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			p = select.poll()
			p.register(f.stdout)

			while True:
				if p.poll(1):
					print(f.stdout.readline())
				time.sleep(1)

		elif platform.system() == 'Windows':
			a=1

		elif platform.system() == 'Darwin':
			a=1
		
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

	def tray_update(self):
		if self.version < self.latestVersion:
			# todo make update link
			self.shutdown(update=True, restart=True)
			self.set_icon()
		else:
			icon = os.path.join(os.path.dirname(sys.argv[0]), 'logo_tray.ico')
			hover_text = 'YAP' + ' - No Update Available'
			self.set_icon()
			
	def set_icon(self):
		logger.info("set icon")
		if self.version < self.latestVersion:
			icon = os.path.abspath('logo_tray-update.ico')
			hover_text = 'YAP' + ' - Update Available!'
			self.setIcon(self.updateIcon)

		else:
			icon = os.path.abspath('logo_tray.ico')
			hover_text = 'YAP'
			self.setIcon(self.validIcon)
		logger.info("icon 2")
		return

	def detect_install(self):
		logger.info("Detect install")
		if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvProxy.py')):
			logger.info("Detect python")
			self.type = ""
			return
		elif platform.system() == 'Linux':
			self.type = "Linux/"
			if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvProxy')):
				logger.info("Detect linux exe")
				return
		elif platform.system() == 'Windows':
			self.type = "Windows/"
			if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvproxy.exe')):
				logger.info("Detect win exe")
				return
		elif platform.system() == 'Darwin':
			self.type = "Macintosh/"
			if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'sstvproxy')):
				logger.info("Detect mac exe")
				return
		logger.info('installing')
		self.assign_latestFile()
		self.shutdown(update=True, install=True)


	def check_install(self):
		logger.debug("Check install")
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
			logger.info(self.url)

	def tray_open(self):
		self.launch_browser()

	def tray_check_update(self):
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
		logger.info("Saving data")
		config = {'version':self.version,'type':self.type,'branch':self.branch}
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'launcher.json'), 'w') as fp:
			json.dump(config, fp)

	def tray_start(self):
		if self.type == "":
			import sstvProxy
			self.yap = multiprocessing.Process(target=sstvProxy.main)
			self.yap.start()
		elif self.type == "Linux/": subprocess.Popen(os.path.abspath("sstvProxy"), stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		#elif self.type == "Linux/": os.spawnl(sys.executable, os.path.abspath("sstvProxy"))
		elif self.type == "Windows/": subprocess.Popen([".\sstvproxy.exe", "-d"], cwd=os.getcwd())
		elif self.type == "Macintosh/": subprocess.Popen(os.path.abspath("sstvproxy"), stdout=subprocess.PIPE,stderr=subprocess.PIPE) #os.execv(sys.executable, ["./sstvproxy", "-d"])
		self.start = True
		self.createMenu(True)


	def tray_restart(self):
		self.shutdown(restart=True)

	def tray_quit(self):
		self.shutdown()

	def tray_cache(self):
		shutil.rmtree(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), ignore_errors=True)

	def tray_logs(self):
		try:
			import webbrowser
			webbrowser.open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'status.log'))
		except Exception as e:
			logger.error(u"Could not open logs: %s" % e)

	def tray_branch(self):
		self.branch = not self.branch
		self.shutdown(update=True, restart=True)

	def launch_browser(self):
		try:
			import webbrowser
			self.gather_yap()
			webbrowser.open('%s%s' % (self.SERVER_HOST,'/sstv/index.html'))
		except Exception as e:
			logger.error(u"Could not launch browser: %s" % e)

	def shutdown(self, restart=False, update=False, install=False):
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
			logger.debug("Gathering version")
			self.version = float(json.loads(urllib.request.urlopen(self.url).read().decode('utf-8'))['Version'])
			self.save_data()
			if install and platform.system() == 'Linux':
				os.chmod(os.path.join(os.path.dirname(sys.argv[0]), ntpath.basename(url)), 0o777)

		if restart:
			os.system('cls' if os.name == 'nt' else 'clear')
			logger.info(u"YAP is restarting...")
			self.tray_start()



def main():
	app = QtGui.QApplication(sys.argv)

	w = QtGui.QWidget()
	trayIcon = SystemTrayIcon(QtGui.QIcon('logo_tray.ico'), w)
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	trayIcon.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()

