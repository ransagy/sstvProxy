from setuptools import setup
from setuptools.command.install import install
import os, platform



class PostInstallCommand(install):
	"""Post-installation for installation mode."""
	def run(self):
		usr = os.path.expanduser("~")
		if platform.system() == 'Linux':
			try:
				os.system("sudo apt-get install python3-tk")
			except:
				print("tkinter install failed")
		elif platform.system() == 'Darwin':
			try:
				os.system('ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null 2> /dev/null ; brew install caskroom/cask/brew-cask 2> /dev/null')
				os.system('brew cask install tcl')
			except:
				print("tkinter install failed")
		if not os.path.isdir(os.path.join(usr, 'YAP')):
			os.mkdir(os.path.join(usr, 'YAP'))
		with open(os.path.join(usr, 'YAP', 'sstvProxy.py'), "wb") as file:
			# get request
			from requests import get
			response = get("https://raw.githubusercontent.com/vorghahn/sstvProxy/master/sstvProxy.py")
			# write to file
			file.write(response.content)


setup(
	name = 'YAPSSTV',
	version = '1.3',
	cmdclass = {'install': PostInstallCommand},
	description = 'Yet Another Proxy',
	python_requires = '>=3.5',
	install_requires=['requests','flask']
)