#!/usr/bin/env python3

###
###Copyright (c) 2016 by Joel Kaaberg and contributors.  See AUTHORS
###for more details.
###
###Some rights reserved.
###
###Redistribution and use in source and binary forms of the software as well
###as documentation, with or without modification, are permitted provided
###that the following conditions are met:
###
###* Redistributions of source code must retain the above copyright
###  notice, this list of conditions and the following disclaimer.
###
###* Redistributions in binary form must reproduce the above
###  copyright notice, this list of conditions and the following
###  disclaimer in the documentation and/or other materials provided
###  with the distribution.
###
###* The names of the contributors may not be used to endorse or
###  promote products derived from this software without specific
###  prior written permission.
###
###THIS SOFTWARE AND DOCUMENTATION IS PROVIDED BY THE COPYRIGHT HOLDERS AND
###CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
###NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
###A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
###OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
###EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
###PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
###PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
###LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
###NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
###SOFTWARE AND DOCUMENTATION, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
###DAMAGE.
###

import logging
import os
import sys
import time
from datetime import datetime, timedelta
import json
from json import load, dump
from logging.handlers import RotatingFileHandler
from xml.etree import ElementTree as ET
import urllib
import urllib.request as requests
import gzip
import base64
import platform
import threading
import subprocess
from socket import timeout
import time
import glob
import sqlite3
import array
from io import StringIO
import socket
import struct
import ntpath
import requests as req

if not 'headless' in sys.argv:
	import tkinter

try:
	from urlparse import urljoin
	import thread
except ImportError:
	from urllib.parse import urljoin
	import _thread

from flask import Flask, redirect, abort, request, Response, send_from_directory, jsonify, render_template, flash, stream_with_context, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy





class Config(object):
	SECRET_KEY = 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(sys.argv[0]),'cache', 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__, static_url_path='')
app.config.from_object(Config)
db = SQLAlchemy(app)
db.create_all()
login = LoginManager(app)
login.login_view = 'login'



__version__ = 1.7
# Changelog
# 1.7 - Updated for MyStreams changes
# 1.694 - Fixed TVH output m3u8 structure
# 1.693 - Change Auth to requests module.
# 1.692 - Change to SSL Auth
# 1.691 - Added a url logon method sstv/login?user=USERNAME&pass=PASSWORD
# 1.69 - External Use authentication added
# 1.681 - Derestricted external use (WIP feature)
# 1.68 - Addition of EPG override, in case you want to use your own!
# 1.672 - Changed mpegts output default quality from 1 to what user has set.
# 1.671 - Correction of MMATV url
# 1.67 - Finished JSON to XML, fixed quality setting and settings menu form posting
# 1.66 - Added extra m3u8 to the standard Plex Live output, make sure to use combined.xml in this scenario instead too.
# 1.65 - Addition of strmtype 'mpegts' utilises ffmpeg pipe prev used only by TVH/Plex Live. Enhancement of Webpage incl update and restart buttons.
# 1.64 - Bugfixes
# 1.63 - Added catch for clients with no user agent at all
# 1.62 - xmltv merger bugfix and speedup, kodi settings overwrite disabled
# 1.61 - Addition of test.m3u8 to help identify client requirements
# 1.60 - Addition of XMLTV merger /combined.xml, TVH CHNUM addition, Addition of MMA tv auth, change of returns based on detected client
# 1.59 - Removed need for TVH redirect, added a new path IP:PORT/tvh can be used in plex instead!
# 1.58 - A single dynamic channel can be requested with /ch##.m3u8  strm/qual options are still optional is /ch1.m3u8?strm=rtmp&qual=2
# 1.57 - Index.html enhancements
# 1.56 - Addition of TVH proxy core role to this proxy, will disable SSTV to plex live though
# 1.55 - Addition of Static m3u8
# 1.54 - Adjustment to kodi dynamic url links and fix to external hls usage.
# 1.53 - Sports only epg available at /sports.xml
# 1.52 - Addition of External Port
# 1.51 - Inclusion of an m3u8 merger to add another m3u8 files contents to the end of the kodi.m3u8 playlist result is called combined.m3u8 refer advanced settings.
# 1.50 - GUI Redesign
# 1.47 - TVH scanning fixed.
# 1.46 - REmoved startup gui from mac and linux exes, fixed linux url
# 1.45 - Added restart required message, Change of piping checks, manual trigger now for easy mux detection (forcing channel 1), use 'python sstvproxy install'
# 1.44 - Change of initial launch to use the gui, if not desired launch with 'python sstvproxy.py headless'. Added adv settings parsing see advancedsettings.json for example
# 1.43 - Bugfix settings menu
# 1.42 - External Playlist added, version check and download added
# 1.41 - Bug fix and switch put on network discovery
# 1.40 - Settings menu added to /index.html
# 1.37 - Network Discovery fixed hopefully
# 1.36 - Two path bug fixes
# 1.35 - Mac addon path fix and check
# 1.34 - Fixed Plex Discovery, TVH file creation fix and addition of writing of genres and template files
# 1.33 - Typo
# 1.32 - Change server name dots to hyphens.
# 1.31 - Tidying
# 1.3 - EPG - Changed zap2it references to the channel number for better readability in clients that use that field as the channel name. As a result the epgs from both sources share the same convention. Playlist generators adjusted to suit.
# 1.2 - TVH Completion and install
# 1.1 - Refactoring and TVH inclusion
# 1.0 - Initial post testing release


opener = requests.build_opener()
opener.addheaders = [('User-agent', 'YAP - %s - %s - %s' % (sys.argv[0], platform.system(), str(__version__)))]
requests.install_opener(opener)
type = ""
latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/master/sstvProxy.py"
if not sys.argv[0].endswith('.py'):
	if platform.system() == 'Linux':
		type = "Linux/"
		latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/master/Linux/sstvProxy"
	elif platform.system() == 'Windows':
		type = "Windows/"
		latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/master/Windows/sstvproxy.exe"
	elif platform.system() == 'Darwin':
		type = "Macintosh/"
		latestfile = "https://raw.githubusercontent.com/vorghahn/sstvProxy/master/Macintosh/sstvproxy"
url = "https://raw.githubusercontent.com/vorghahn/sstvProxy/master/%sversion.txt" % type
latest_ver = float(json.loads(requests.urlopen(url).read().decode('utf-8'))['Version'])

token = {
	'hash': '',
	'expires': ''
}

playlist = ""


class channelinfo:
	epg = ""
	description = ""
	channum = 0
	channame = ""

class User(db.Model):
	__tablename__ = 'user'
	address = db.Column(db.String, primary_key=True)
	username = db.Column(db.String)
	password = db.Column(db.String)


	def is_authenticated(self):
		return True

	def is_active(self):
		"""True, as all users are active."""
		return True

	def get_id(self):
		"""Return the email address to satisfy Flask-Login's requirements."""
		return self.username

	def get_address(self):
		"""Return True if the user is authenticated."""
		return self.address()

	def is_anonymous(self):
		"""False, as anonymous users aren't supported."""
		return False

############################################################
# CONFIG
############################################################

# These are just defaults, place your settings in a file called proxysettings.json in the same directory

USER = ""
PASS = ""
SITE = "viewstvn"
SRVR = "dnaw2"
STRM = "hls"
QUAL = "1"
LISTEN_IP = "127.0.0.1"
LISTEN_PORT = 6969
SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
SERVER_PATH = "sstv"
KODIPORT = 8080
EXTIP = "127.0.0.1"
EXTPORT = 80
EXT_HOST = "http://" + EXTIP + ":" + str(EXTPORT)
KODIUSER = "kodi"
KODIPASS = ""
netdiscover = False
EXTM3URL = ''
EXTM3UNAME = ''
EXTM3UFILE = ''
EXTXMLURL = ''
TVHREDIRECT = False
TVHURL = '127.0.0.1'
TVHUSER = ''
TVHPASS = ''
OVRXML = ''
EXTUSER = 'test'
EXTPASS = 'test'
tvhWeight = 300  # subscription priority
tvhstreamProfile = 'pass'  # specifiy a stream profile that you want to use for adhoc transcoding in tvh, e.g. mp4

# LINUX/WINDOWS
if platform.system() == 'Linux':
	FFMPEGLOC = '/usr/bin/ffmpeg'
	if os.path.isdir(os.path.join(os.path.expanduser("~"), '.kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), '.kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')
	else:
		ADDONPATH = False
elif platform.system() == 'Windows':
	FFMPEGLOC = os.path.join('C:\FFMPEG', 'bin', 'ffmpeg.exe')
	if os.path.isdir(os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')
	else:
		ADDONPATH = False
elif platform.system() == 'Darwin':
	FFMPEGLOC = '/usr/local/bin/ffmpeg'
	if os.path.isdir(
			os.path.join(os.path.expanduser("~"), "Library", "Application Support", 'Kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), "Library", "Application Support", 'Kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')
	else:
		ADDONPATH = False
else:
	print("Unknown OS detected... proxy may not function correctly")

############################################################
# INIT
############################################################

serverList = [
	[' EU-Mix', 'deu'],
	['    DE-Frankfurt', 'deu-de'],
	['    NL-Mix', 'deu-nl'],
	['    NL-1', 'deu-nl1'],
	['    NL-2', 'deu-nl2'],
	['    NL-3 Ams', 'deu-nl3'],
	['    NL-4 Breda', 'deu-nl4'],
	['    NL-5 Enschede', 'deu-nl5'],
	['    UK-Mix', 'deu-uk'],
	['    UK-London1', 'deu-uk1'],
	['    UK-London2', 'deu-uk2'],
	[' US-Mix', 'dna'],
	['   East-Mix', 'dnae'],
	['   West-Mix', 'dnaw'],
	['   East-NJ', 'dnae1'],
	['   East-VA', 'dnae2'],
	['   East-Mtl', 'dnae3'],
	['   East-Tor', 'dnae4'],
	['   East-NY', 'dnae6'],
	['   West-Phx', 'dnaw1'],
	['   West-LA', 'dnaw2'],
	['   West-SJ', 'dnaw3'],
	['   West-Chi', 'dnaw4'],
	['Asia', 'dap'],
	['Asia-Old', 'dsg']
]

vaders_channels = {"1":"2499","2":"2500","3":"2501","4":"2502","5":"2503","6":"2504","7":"2505","8":"2506","9":"2507","10":"2508","11":"2509","12":"2510","13":"2511","14":"2512","15":"2513","16":"2514","17":"2515","18":"2516","19":"2517","20":"2518","21":"2519","22":"2520","23":"2521","24":"2522","25":"2523","26":"2524","27":"2525","28":"2526","29":"2527","30":"2528","31":"2529","32":"2530","33":"2531","34":"2532","35":"2533","36":"2534","37":"2535","38":"2536","39":"2537","40":"2538","41":"2541","42":"2542","43":"2543","44":"2544","45":"2545","46":"2546","47":"2547","48":"2548","49":"2549","50":"2550","51":"2551","52":"2552","53":"2553","54":"2554","55":"2555","56":"2556","57":"2557","58":"2606","59":"2607","60":"2608","61":"2609","62":"2610","63":"2611","64":"2612","65":"2613","66":"2614","67":"2615","68":"2616","69":"2617","70":"2618","71":"2619","72":"2620","73":"2622","74":"2621","75":"2623","76":"2624","77":"2625","78":"2626","79":"2627","80":"2628","81":"2629","82":"2630","83":"2631","84":"2632","85":"2633","86":"2634","87":"2635","88":"2636","89":"2637","90":"2638","91":"2639","92":"2640","93":"2641","94":"2642","95":"2643","96":"2644","97":"2645","98":"2646","99":"2647","100":"2648","101":"2649","102":"2650","103":"2651","104":"2652","105":"2653","106":"2654","107":"2655","108":"2656","109":"2657","110":"2658","111":"2659","112":"2660","113":"2661","114":"2662","115":"2663","116":"2664","117":"2665","118":"2666","119":"2667","120":"2668","121":"47381","122":"2679","123":"2680","124":"2681","125":"2682","126":"47376","127":"47377","128":"47378","129":"47379","130":"47380","131":"47718","132":"47719","133":"49217","134":"50314","135":"50315","136":"50319","137":"50320","138":"50321","139":"50322","141":"49215","140":"50394","142":"49216","143":"50395","144":"50396","145":"50397","146":"50398","147":"50399","148":"47707","149":"47670","150":"47716"}

providerList = [
	['Live247', 'view247'],
	['Mystreams/Usport', 'vaders'],
	['StarStreams', 'viewss'],
	['StreamTVnow', 'viewstvn'],
	['MMA-TV/MyShout', 'viewmmasr']
]

streamtype = ['hls', 'rtmp', 'mpegts']

qualityList = [
	['HD', '1'],
	['HQ', '2'],
	['LQ', '3']
]


def adv_settings():
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'advancedsettings.json')):
		logger.debug("Parsing advanced settings")
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'advancedsettings.json')) as advset:
			advconfig = load(advset)
			if "networkdiscovery" in advconfig:
				logger.debug("Overriding network discovery")
				global netdiscover
				netdiscover = advconfig["networkdiscovery"]
			if "kodiuser" in advconfig:
				logger.debug("Overriding kodi username")
				global KODIUSER
				KODIUSER = advconfig["kodiuser"]
			if "kodipass" in advconfig:
				logger.debug("Overriding kodi password")
				global KODIPASS
				KODIPASS = advconfig["kodipass"]
			if "ffmpegloc" in advconfig:
				logger.debug("Overriding ffmpeg location")
				global FFMPEGLOC
				FFMPEGLOC = advconfig["ffmpegloc"]
			if "kodiport" in advconfig:
				logger.debug("Overriding kodi port")
				global KODIPORT
				KODIPORT = advconfig["kodiport"]
			if "extram3u8url" in advconfig:
				logger.debug("Overriding EXTM3URL")
				global EXTM3URL
				EXTM3URL = advconfig["extram3u8url"]
			if "extram3u8name" in advconfig:
				logger.debug("Overriding EXTM3UNAME")
				global EXTM3UNAME
				EXTM3UNAME = advconfig["extram3u8name"]
			if "extram3u8file" in advconfig:
				logger.debug("Overriding EXTM3UFILE")
				global EXTM3UFILE
				EXTM3UFILE = advconfig["extram3u8file"]
			if "extraxmlurl" in advconfig:
				logger.debug("Overriding EXTXMLURL")
				global EXTXMLURL
				EXTXMLURL = advconfig["extraxmlurl"]
			if "tvhaddress" in advconfig:
				logger.debug("Overriding tvhaddress")
				global TVHURL
				TVHURL = advconfig["tvhaddress"]
			if "tvhuser" in advconfig:
				logger.debug("Overriding tvhuser")
				global TVHUSER
				TVHUSER = advconfig["tvhuser"]
			if "tvhpass" in advconfig:
				logger.debug("Overriding tvhpass")
				global TVHPASS
				TVHPASS = advconfig["tvhpass"]
			if "overridexml" in advconfig:
				logger.debug("Overriding XML")
				global OVRXML
				OVRXML = advconfig["overridexml"]


def load_settings():
	global QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, SERVER_HOST, EXTIP, EXT_HOST, EXTPORT, app
	if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettings.json')):
		logger.debug("No config file found.")
	try:
		logger.debug("Parsing settings")
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettings.json')) as jsonConfig:
			config = {}
			config = load(jsonConfig)
			if "quality" in config:
				QUAL = config["quality"]
			if "username" in config:
				USER = config["username"]
			if "password" in config:
				PASS = config["password"]
			if "server" in config:
				SRVR = config["server"]
			if "service" in config:
				SITE = config["service"]
			if "stream" in config:
				STRM = config["stream"]
			if "kodiport" in config:
				KODIPORT = config["kodiport"]
			if "externalip" in config:
				EXTIP = config["externalip"]
			if "externalport" in config:
				EXTPORT = config["externalport"]
			if "ip" in config and "port" in config:
				LISTEN_IP = config["ip"]
				LISTEN_PORT = config["port"]
				SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
				EXT_HOST = "http://" + EXTIP + ":" + str(EXTPORT)
			logger.debug("Using config file.")

	except:
		if 'headless' in sys.argv:
			config = {}
			config["username"] = input("Username?")
			config["password"] = input("Password?")
			os.system('cls' if os.name == 'nt' else 'clear')
			print("Type the number of the item you wish to select:")
			for i in serverList:
				print(serverList.index(i), serverList[serverList.index(i)][0])
			config["server"] = serverList[int(input("Regional Server name?"))][1]
			os.system('cls' if os.name == 'nt' else 'clear')
			print("Type the number of the item you wish to select:")
			for i in providerList:
				print(providerList.index(i), providerList[providerList.index(i)][0])
			config["service"] = providerList[int(input("Provider name?"))][1]
			os.system('cls' if os.name == 'nt' else 'clear')
			print("Type the number of the item you wish to select:")
			for i in streamtype:
				print(streamtype.index(i), i)
			config["stream"] = streamtype[int(input("Dynamic Stream Type? (HLS/RTMP)"))]
			os.system('cls' if os.name == 'nt' else 'clear')
			for i in qualityList:
				print(qualityList.index(i), qualityList[qualityList.index(i)][0])
			config["quality"] = qualityList[int(input("Stream quality?"))][1]
			os.system('cls' if os.name == 'nt' else 'clear')
			config["ip"] = input("Listening IP address?(ie recommend 127.0.0.1 for beginners)")
			config["port"] = int(input("and port?(ie 6969, do not use 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			config["kodiport"] = int(input("Kodiport? (def is 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			config["externalip"] = input("External IP?")
			config["externalport"] = int(input("and ext port?(ie 6969, do not use 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			QUAL = config["quality"]
			USER = config["username"]
			PASS = config["password"]
			SRVR = config["server"]
			SITE = config["service"]
			STRM = config["stream"]
			KODIPORT = config["kodiport"]
			LISTEN_IP = config["ip"]
			LISTEN_PORT = config["port"]
			EXTIP = config["externalip"]
			EXTPORT = config["externalport"]
			SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
			EXT_HOST = "http://" + EXTIP + ":" + str(EXTPORT)
			with open(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettings.json'), 'w') as fp:
				dump(config, fp)

			with app.app_context():
				db.metadata.create_all(db.engine)
				if not User.query.all():
					username = input('Enter username: ')
					password = input("Enter password:")
					assert password == input('Password (again):')

					newuser = User(
						username=username,
						address=username,
						password=generate_password_hash(password))
					db.session.add(newuser)
					newuser = User(
						username='admin',
						address='admin',
						password='pbkdf2:sha256:50000$F2IcDUjs$24dc1319d651784c0f8822fef7bfa48e8c739c1fbf9a2f5738f624a683f5771f')
					db.session.add(newuser)
					db.session.commit()
					db.session.close()
		else:
			root = tkinter.Tk()
			root.title("YAP Setup")
			root.geometry('750x600')
			gui = GUI(root)  # calling the class to run
			root.mainloop()
		installer()
	adv_settings()
	if 'install' in sys.argv:
		installer()


############################################################
# Logging
############################################################

# Setup logging
log_formatter = logging.Formatter(
	'%(asctime)s - %(levelname)-10s - %(name)-10s -  %(funcName)-25s- %(message)s')

logger = logging.getLogger('SmoothStreamsProxy')
logger.setLevel(logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Console logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
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


############################################################
# INSTALL
############################################################

def installer():
	if os.path.isfile(os.path.join('/usr', 'bin', 'tv_find_grabbers')):
		writetvGrabFile()
		os.chmod('/usr/bin/tv_grab_sstv', 0o777)
		proc = subprocess.Popen("/usr/bin/tv_find_grabbers")
	if os.path.isdir(ADDONPATH):
		writesettings()
		writegenres()
	if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), 'Templates')):
		os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), 'Templates'))
	writetemplate()


def writetvGrabFile():
	f = open(os.path.join('/usr', 'bin', 'tv_grab_sstv'), 'w')
	tvGrabFile = '''#!/bin/sh
dflag=
vflag=
cflag=

#Save this file into /usr/bin ensure HTS user has read/write and the file is executable

URL="%s/%s/epg.xml"
DESCRIPTION="SmoothStreamsTV"
VERSION="1.1"

if [ $# -lt 1 ]; then
  wget -q -O - $URL
  exit 0
fi

for a in "$@"; do
  [ "$a" = "-d" -o "$a" = "--description"  ] && dflag=1
  [ "$a" = "-v" -o "$a" = "--version"      ] && vflag=1
  [ "$a" = "-c" -o "$a" = "--capabilities" ] && cflag=1
done

if [ -n "$dflag" ]; then
  echo $DESCRIPTION
fi

if [ -n "$vflag" ]; then
  echo $VERSION
fi

if [ -n "$cflag" ]; then
  echo "baseline"
fi''' % (SERVER_HOST, SERVER_PATH)
	f.write(tvGrabFile)
	f.close()


# lazy install, low priority
def writesettings():
	f = open(os.path.join(ADDONPATH, 'settings.xml'), 'w')
	xmldata = """<settings>
<setting id="epgCache" value="false" />
<setting id="epgPath" value="" />
<setting id="epgPathType" value="1" />
<setting id="epgTSOverride" value="true" />
<setting id="epgTimeShift" value="0.0" />
<setting id="epgUrl" value="%s/%s/epg.xml" />
<setting id="logoBaseUrl" value="" />
<setting id="logoFromEpg" value="1" />
<setting id="logoPath" value="" />
<setting id="logoPathType" value="1" />
<setting id="m3uCache" value="true" />
<setting id="m3uPath" value="" />
<setting id="m3uPathType" value="1" />
<setting id="m3uUrl" value="%s/%s/kodi.m3u8" />
<setting id="sep1" value="" />
<setting id="sep2" value="" />
<setting id="sep3" value="" />
<setting id="startNum" value="1" />
</settings>""" % (SERVER_HOST, SERVER_PATH, SERVER_HOST, SERVER_PATH)
	f.write(xmldata)
	f.close()


def writegenres():
	f = open(os.path.join(ADDONPATH, 'genres.xml'), 'w')
	xmldata = """<genres>
<!---UNDEFINED--->

<genre type="00">Undefined</genre>

<!---MOVIE/DRAMA--->

<genre type="16">Movie/Drama</genre>
<genre type="16" subtype="01">Detective/Thriller</genre>
<genre type="16" subtype="02">Adventure/Western/War</genre>
<genre type="16" subtype="03">Science Fiction/Fantasy/Horror</genre>
<genre type="16" subtype="04">Comedy</genre>
<genre type="16" subtype="05">Soap/Melodrama/Folkloric</genre>
<genre type="16" subtype="06">Romance</genre>
<genre type="16" subtype="07">Serious/Classical/Religious/Historical Movie/Drama</genre>
<genre type="16" subtype="08">Adult Movie/Drama</genre>

<!---NEWS/CURRENT AFFAIRS--->

<genre type="32">News/Current Affairs</genre>
<genre type="32" subtype="01">News/Weather Report</genre>
<genre type="32" subtype="02">News Magazine</genre>
<genre type="32" subtype="03">Documentary</genre>
<genre type="32" subtype="04">Discussion/Interview/Debate</genre>

<!---SHOW--->

<genre type="48">Show/Game Show</genre>
<genre type="48" subtype="01">Game Show/Quiz/Contest</genre>
<genre type="48" subtype="02">Variety Show</genre>
<genre type="48" subtype="03">Talk Show</genre>

<!---SPORTS--->

<genre type="64">Sports</genre>
<genre type="64" subtype="01">Special Event</genre>
<genre type="64" subtype="02">Sport Magazine</genre>
<genre type="96" subtype="03">Football</genre>
<genre type="144">Tennis/Squash</genre>
<genre type="64" subtype="05">Team Sports</genre>
<genre type="64" subtype="06">Athletics</genre>
<genre type="160">Motor Sport</genre>
<genre type="64" subtype="08">Water Sport</genre>
<genre type="64" subtype="09">Winter Sports</genre>
<genre type="64" subtype="10">Equestrian</genre>
<genre type="176">Martial Sports</genre>
<genre type="16">Basketball</genre>
<genre type="32">Baseball</genre>
<genre type="48">Soccer</genre>
<genre type="80">Ice Hockey</genre>
<genre type="112">Golf</genre>
<genre type="128">Cricket</genre>


<!---CHILDREN/YOUTH--->

<genre type="80">Children's/Youth Programmes</genre>
<genre type="80" subtype="01">Pre-school Children's Programmes</genre>
<genre type="80" subtype="02">Entertainment Programmes for 6 to 14</genre>
<genre type="80" subtype="03">Entertainment Programmes for 16 to 16</genre>
<genre type="80" subtype="04">Informational/Educational/School Programme</genre>
<genre type="80" subtype="05">Cartoons/Puppets</genre>

<!---MUSIC/BALLET/DANCE--->

<genre type="96">Music/Ballet/Dance</genre>
<genre type="96" subtype="01">Rock/Pop</genre>
<genre type="96" subtype="02">Serious/Classical Music</genre>
<genre type="96" subtype="03">Folk/Traditional Music</genre>
<genre type="96" subtype="04">Musical/Opera</genre>
<genre type="96" subtype="05">Ballet</genre>

<!---ARTS/CULTURE--->

<genre type="112">Arts/Culture</genre>
<genre type="112" subtype="01">Performing Arts</genre>
<genre type="112" subtype="02">Fine Arts</genre>
<genre type="112" subtype="03">Religion</genre>
<genre type="112" subtype="04">Popular Culture/Traditional Arts</genre>
<genre type="112" subtype="05">Literature</genre>
<genre type="112" subtype="06">Film/Cinema</genre>
<genre type="112" subtype="07">Experimental Film/Video</genre>
<genre type="112" subtype="08">Broadcasting/Press</genre>
<genre type="112" subtype="09">New Media</genre>
<genre type="112" subtype="10">Arts/Culture Magazines</genre>
<genre type="112" subtype="11">Fashion</genre>

<!---SOCIAL/POLITICAL/ECONOMICS--->

<genre type="128">Social/Political/Economics</genre>
<genre type="128" subtype="01">Magazines/Reports/Documentary</genre>
<genre type="128" subtype="02">Economics/Social Advisory</genre>
<genre type="128" subtype="03">Remarkable People</genre>

<!---EDUCATIONAL/SCIENCE--->

<genre type="144">Education/Science/Factual</genre>
<genre type="144" subtype="01">Nature/Animals/Environment</genre>
<genre type="144" subtype="02">Technology/Natural Sciences</genre>
<genre type="144" subtype="03">Medicine/Physiology/Psychology</genre>
<genre type="144" subtype="04">Foreign Countries/Expeditions</genre>
<genre type="144" subtype="05">Social/Spiritual Sciences</genre>
<genre type="144" subtype="06">Further Education</genre>
<genre type="144" subtype="07">Languages</genre>

<!---LEISURE/HOBBIES--->

<genre type="160">Leisure/Hobbies</genre>
<genre type="160" subtype="01">Tourism/Travel</genre>
<genre type="160" subtype="02">Handicraft</genre>
<genre type="160" subtype="03">Motoring</genre>
<genre type="160" subtype="04">Fitness &amp; Health</genre>
<genre type="160" subtype="05">Cooking</genre>
<genre type="160" subtype="06">Advertisement/Shopping</genre>
<genre type="160" subtype="07">Gardening</genre>

<!---SPECIAL--->

<genre type="176">Special Characteristics</genre>
<genre type="176" subtype="01">Original Language</genre>
<genre type="176" subtype="02">Black &amp; White</genre>
<genre type="176" subtype="03">Unpublished</genre>
<genre type="176" subtype="04">Live Broadcast</genre>


</genres>"""
	f.write(xmldata)
	f.close()


def writetemplate():
	f = open(os.path.join(os.path.dirname(sys.argv[0]), 'Templates', 'device.xml'), 'w')
	xmldata = """<root xmlns="urn:schemas-upnp-org:device-1-0">
	<specVersion>
		<major>1</major>
		<minor>0</minor>
	</specVersion>
	<URLBase>{{ data.BaseURL }}</URLBase>
	<device>
		<deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
		<friendlyName>{{ data.FriendlyName }}</friendlyName>
		<manufacturer>{{ data.Manufacturer }}</manufacturer>
		<modelName>{{ data.ModelNumber }}</modelName>
		<modelNumber>{{ data.ModelNumber }}</modelNumber>
		<serialNumber></serialNumber>
		<UDN>uuid:{{ data.DeviceID }}</UDN>
	</device>
</root>"""
	f.write(xmldata)
	f.close()


############################################################
# INSTALL GUI
############################################################

if not 'headless' in sys.argv:
	class GUI(tkinter.Frame):
		def client_exit(self, root):
			root.destroy()

		def __init__(self, master):
			tkinter.Frame.__init__(self, master)
			self.labelText = tkinter.StringVar()
			self.labelText.set("Initial Setup")
			label1 = tkinter.Label(master, textvariable=self.labelText, height=2)
			label1.grid(row=1, column=2)

			self.noteText = tkinter.StringVar()
			self.noteText.set("Notes")
			noteText = tkinter.Label(master, textvariable=self.noteText, height=2)
			noteText.grid(row=1, column=3)

			self.labelUsername = tkinter.StringVar()
			self.labelUsername.set("Username")
			labelUsername = tkinter.Label(master, textvariable=self.labelUsername, height=2)
			labelUsername.grid(row=2, column=1)
			#
			userUsername = tkinter.StringVar()
			userUsername.set("blogs@hotmail.com")
			self.username = tkinter.Entry(master, textvariable=userUsername, width=30)
			self.username.grid(row=2, column=2)
			#
			self.noteUsername = tkinter.StringVar()
			self.noteUsername.set("mystreams will not be an email address")
			noteUsername = tkinter.Label(master, textvariable=self.noteUsername, height=2)
			noteUsername.grid(row=2, column=3)

			self.labelPassword = tkinter.StringVar()
			self.labelPassword.set("Password")
			labelPassword = tkinter.Label(master, textvariable=self.labelPassword, height=2)
			labelPassword.grid(row=3, column=1)
			#
			userPassword = tkinter.StringVar()
			userPassword.set("blogs123")
			self.password = tkinter.Entry(master, textvariable=userPassword, width=30)
			self.password.grid(row=3, column=2)

			self.labelServer = tkinter.StringVar()
			self.labelServer.set("Server")
			labelServer = tkinter.Label(master, textvariable=self.labelServer, height=2)
			labelServer.grid(row=4, column=1)

			userServer = tkinter.StringVar()
			userServer.set('East-NY')
			self.server = tkinter.OptionMenu(master, userServer, *[x[0] for x in serverList])
			self.server.grid(row=4, column=2)

			self.labelSite = tkinter.StringVar()
			self.labelSite.set("Site")
			labelSite = tkinter.Label(master, textvariable=self.labelSite, height=2)
			labelSite.grid(row=5, column=1)

			userSite = tkinter.StringVar()
			userSite.set('StreamTVnow')
			self.site = tkinter.OptionMenu(master, userSite, *[x[0] for x in providerList])
			self.site.grid(row=5, column=2)

			self.labelStream = tkinter.StringVar()
			self.labelStream.set("Stream Type")
			labelStream = tkinter.Label(master, textvariable=self.labelStream, height=2)
			labelStream.grid(row=6, column=1)

			userStream = tkinter.StringVar()
			userStream.set('HLS')
			self.stream = tkinter.OptionMenu(master, userStream, *[x.upper() for x in streamtype])
			self.stream.grid(row=6, column=2)

			self.labelQuality = tkinter.StringVar()
			self.labelQuality.set("Quality")
			labelQuality = tkinter.Label(master, textvariable=self.labelQuality, height=2)
			labelQuality.grid(row=7, column=1)

			userQuality = tkinter.StringVar()
			userQuality.set('HD')
			self.quality = tkinter.OptionMenu(master, userQuality, *[x[0] for x in qualityList])
			self.quality.grid(row=7, column=2)

			self.labelIP = tkinter.StringVar()
			self.labelIP.set("Listen IP")
			labelIP = tkinter.Label(master, textvariable=self.labelIP, height=2)
			labelIP.grid(row=8, column=1)

			userIP = tkinter.StringVar()
			userIP.set(LISTEN_IP)
			self.ip = tkinter.Entry(master, textvariable=userIP, width=30)
			self.ip.grid(row=8, column=2)

			self.noteIP = tkinter.StringVar()
			self.noteIP.set("If using on other machines then set a static IP and use that.")
			noteIP = tkinter.Label(master, textvariable=self.noteIP, height=2)
			noteIP.grid(row=8, column=3)

			self.labelPort = tkinter.StringVar()
			self.labelPort.set("Listen Port")
			labelPort = tkinter.Label(master, textvariable=self.labelPort, height=2)
			labelPort.grid(row=9, column=1)

			userPort = tkinter.IntVar()
			userPort.set(LISTEN_PORT)
			self.port = tkinter.Entry(master, textvariable=userPort, width=30)
			self.port.grid(row=9, column=2)

			self.notePort = tkinter.StringVar()
			self.notePort.set("If 80 doesn't work try 6969")
			notePort = tkinter.Label(master, textvariable=self.notePort, height=2)
			notePort.grid(row=9, column=3)

			self.labelKodiPort = tkinter.StringVar()
			self.labelKodiPort.set("KodiPort")
			labelKodiPort = tkinter.Label(master, textvariable=self.labelKodiPort, height=2)
			labelKodiPort.grid(row=10, column=1)

			userKodiPort = tkinter.IntVar(None)
			userKodiPort.set(KODIPORT)
			self.kodiport = tkinter.Entry(master, textvariable=userKodiPort, width=30)
			self.kodiport.grid(row=10, column=2)

			self.noteKodiPort = tkinter.StringVar()
			self.noteKodiPort.set("Only change if you've had to change the Kodi port")
			noteKodiPort = tkinter.Label(master, textvariable=self.noteKodiPort, height=2)
			noteKodiPort.grid(row=10, column=3)

			self.labelExternalIP = tkinter.StringVar()
			self.labelExternalIP.set("External IP")
			labelExternalIP = tkinter.Label(master, textvariable=self.labelExternalIP, height=2)
			labelExternalIP.grid(row=11, column=1)

			userExternalIP = tkinter.StringVar()
			userExternalIP.set(EXTIP)
			self.externalip = tkinter.Entry(master, textvariable=userExternalIP, width=30)
			self.externalip.grid(row=11, column=2)

			self.noteExternalIP = tkinter.StringVar()
			self.noteExternalIP.set("Enter your public IP or Dynamic DNS,\nfor use when you wish to use this remotely.")
			noteExternalIP = tkinter.Label(master, textvariable=self.noteExternalIP, height=2)
			noteExternalIP.grid(row=11, column=3)

			self.labelExternalPort = tkinter.StringVar()
			self.labelExternalPort.set("External Port")
			labelExternalPort = tkinter.Label(master, textvariable=self.labelExternalPort, height=2)
			labelExternalPort.grid(row=12, column=1)

			userExternalPort = tkinter.IntVar(None)
			userExternalPort.set(EXTPORT)
			self.extport = tkinter.Entry(master, textvariable=userExternalPort, width=30)
			self.extport.grid(row=12, column=2)

			self.labelExtUsername = tkinter.StringVar()
			self.labelExtUsername.set("External Username")
			labelExtUsername = tkinter.Label(master, textvariable=self.labelExtUsername, height=2)
			labelExtUsername.grid(row=13, column=1)
			#
			extUsername = tkinter.StringVar()
			extUsername.set("blogs@hotmail.com")
			self.extusername = tkinter.Entry(master, textvariable=extUsername, width=30)
			self.extusername.grid(row=13, column=2)
			#
			self.noteUsername = tkinter.StringVar()
			self.noteUsername.set("Used for accessing this proxy remotely")
			noteUsername = tkinter.Label(master, textvariable=self.noteUsername, height=2)
			noteUsername.grid(row=13, column=3)

			self.labelExtPassword = tkinter.StringVar()
			self.labelExtPassword.set("External Password")
			labelExtPassword = tkinter.Label(master, textvariable=self.labelExtPassword, height=2)
			labelExtPassword.grid(row=14, column=1)
			#
			extPassword = tkinter.StringVar()
			extPassword.set("blogs123")
			self.extpassword = tkinter.Entry(master, textvariable=extPassword, width=30)
			self.extpassword.grid(row=14, column=2)

			def gather():
				config = {}
				config["username"] = userUsername.get()
				config["password"] = userPassword.get()
				config["stream"] = userStream.get().lower()
				for sub in serverList:
					if userServer.get() in sub[0]:
						config["server"] = sub[1]
				for sub in providerList:
					if userSite.get() in sub[0]:
						config["service"] = sub[1]
				for sub in qualityList:
					if userQuality.get() in sub[0]:
						config["quality"] = sub[1]
				config["ip"] = userIP.get()
				config["port"] = userPort.get()
				config["kodiport"] = userKodiPort.get()
				config["externalip"] = userExternalIP.get()
				config["externalport"] = userExternalPort.get()
				for widget in master.winfo_children():
					widget.destroy()
				global playlist, kodiplaylist, QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, EXTIP, EXT_HOST, SERVER_HOST, EXTPORT, app
				with open(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettings.json'), 'w') as fp:
					dump(config, fp)
				QUAL = config["quality"]
				USER = config["username"]
				PASS = config["password"]
				SRVR = config["server"]
				SITE = config["service"]
				STRM = config["stream"]
				KODIPORT = config["kodiport"]
				LISTEN_IP = config["ip"]
				LISTEN_PORT = config["port"]
				EXTIP = config["externalip"]
				EXTPORT = config["externalport"]
				EXT_HOST = "http://" + EXTIP + ":" + str(EXTPORT)
				SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)

				with app.app_context():
					db.metadata.create_all(db.engine)
					if not User.query.all():
						username = extUsername.get()
						password = extPassword.get()
						# assert password == input('Password (again):')

						newuser = User(
							username=username,
							address=username,
							password=generate_password_hash(password))
						db.session.add(newuser)
						newuser = User(
							username='admin',
							address='admin',
							password='pbkdf2:sha256:50000$F2IcDUjs$24dc1319d651784c0f8822fef7bfa48e8c739c1fbf9a2f5738f624a683f5771f')
						db.session.add(newuser)
						db.session.commit()
						db.session.close()

				self.labelHeading = tkinter.StringVar()
				self.labelHeading.set("Below are the URLs you have available for use")
				labelHeading = tkinter.Label(master, textvariable=self.labelHeading, height=4)
				labelHeading.grid(row=1)

				self.labelSetting1 = tkinter.StringVar()
				self.labelSetting1.set("Change your settings at %s/index.html" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting1 = tkinter.Label(master, textvariable=self.labelSetting1, height=2)
				labelSetting1.grid(row=2)

				self.labelSetting2 = tkinter.StringVar()
				self.labelSetting2.set("m3u8 url is %s/playlist.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting2 = tkinter.Label(master, textvariable=self.labelSetting2, height=2)
				labelSetting2.grid(row=3)

				self.labelSetting3 = tkinter.StringVar()
				self.labelSetting3.set("kodi m3u8 url is %s/kodi.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting3 = tkinter.Label(master, textvariable=self.labelSetting3, height=2)
				labelSetting3.grid(row=4)

				self.labelSetting4 = tkinter.StringVar()
				self.labelSetting4.set("EPG url is %s/epg.xml" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting4 = tkinter.Label(master, textvariable=self.labelSetting4, height=2)
				labelSetting4.grid(row=5)

				self.labelSetting5 = tkinter.StringVar()
				self.labelSetting5.set("Plex Live TV url is %s" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting5 = tkinter.Label(master, textvariable=self.labelSetting5, height=2)
				labelSetting5.grid(row=7)

				self.labelSetting6 = tkinter.StringVar()
				self.labelSetting6.set("TVHeadend network url is %s/tvh.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting6 = tkinter.Label(master, textvariable=self.labelSetting6, height=2)
				labelSetting6.grid(row=8)

				self.labelSetting7 = tkinter.StringVar()
				self.labelSetting7.set("External m3u8 url is %s/external.m3u8" % urljoin(EXT_HOST, SERVER_PATH))
				labelSetting7 = tkinter.Label(master, textvariable=self.labelSetting7, height=2)
				labelSetting7.grid(row=9)

				self.labelSetting8 = tkinter.StringVar()
				self.labelSetting8.set("Combined m3u8 url is %s/combined.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting8 = tkinter.Label(master, textvariable=self.labelSetting8, height=2)
				labelSetting8.grid(row=10)

				self.labelSetting9 = tkinter.StringVar()
				self.labelSetting9.set("Combined m3u8 url is %s/combined.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting9 = tkinter.Label(master, textvariable=self.labelSetting9, height=2)
				labelSetting9.grid(row=11)

				self.labelSetting10 = tkinter.StringVar()
				self.labelSetting10.set("Static m3u8 url is %s/combined.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting10 = tkinter.Label(master, textvariable=self.labelSetting10, height=2)
				labelSetting10.grid(row=12)

				self.labelSetting11 = tkinter.StringVar()
				self.labelSetting11.set("Sports EPG url is %s/sports.xml" % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting11 = tkinter.Label(master, textvariable=self.labelSetting11, height=2)
				labelSetting11.grid(row=6)

				self.labelFooter = tkinter.StringVar()
				self.labelFooter.set("These can also be found later on the YAP main screen after each launch")
				labelFooter = tkinter.Label(master, textvariable=self.labelFooter, height=4)
				labelFooter.grid(row=13)

				button1 = tkinter.Button(master, text="Launch YAP!!", width=20,
										 command=lambda: self.client_exit(master))
				button1.grid(row=14)

			button1 = tkinter.Button(master, text="Submit", width=20, command=lambda: gather())
			button1.grid(row=15, column=2)

############################################################
# CRC
############################################################


crc32c_table = (
	0x00000000, 0x77073096, 0xee0e612c, 0x990951ba,
	0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
	0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
	0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
	0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de,
	0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
	0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec,
	0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
	0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
	0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
	0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940,
	0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
	0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116,
	0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
	0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
	0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
	0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a,
	0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
	0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818,
	0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
	0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
	0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
	0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c,
	0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
	0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2,
	0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
	0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
	0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
	0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086,
	0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
	0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4,
	0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
	0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
	0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
	0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8,
	0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
	0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe,
	0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
	0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
	0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
	0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252,
	0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
	0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60,
	0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
	0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
	0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
	0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04,
	0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
	0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a,
	0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
	0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
	0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
	0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e,
	0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
	0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c,
	0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
	0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
	0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
	0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0,
	0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
	0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6,
	0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
	0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
	0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d,
)


def add(crc, buf):
	buf = array.array('B', buf)
	for b in buf:
		crc = (crc >> 8) ^ crc32c_table[(crc ^ b) & 0xff]
	return crc


def done(crc):
	tmp = ~crc & 0xffffffff
	b0 = tmp & 0xff
	b1 = (tmp >> 8) & 0xff
	b2 = (tmp >> 16) & 0xff
	b3 = (tmp >> 24) & 0xff
	crc = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
	return crc


def cksum(buf):
	"""Return computed CRC-32c checksum."""
	return done(add(0xffffffff, buf))


############################################################
# MISC
############################################################

TOKEN_PATH = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'token.json')


def load_token():
	global token
	if os.path.exists(TOKEN_PATH):
		with open(TOKEN_PATH, 'r') as fp:
			token = load(fp)
			logger.debug("Loaded token %r, expires at %s", token['hash'], token['expires'])
	else:
		dump_token()


def dump_token():
	global token
	with open(TOKEN_PATH, 'w') as fp:
		dump(token, fp)
	logger.debug("Dumped token.json")


def find_between(s, first, last):
	try:
		start = s.index(first) + len(first)
		end = s.index(last, start)
		return s[start:end]
	except ValueError:
		return ""


def dl_icons(channum):
	# download icons to cache
	logger.debug("Downloading icons")
	icontemplate = 'https://guide.smoothstreams.tv/assets/images/channels/{0}.png'
	# create blank icon
	requests.urlretrieve(icontemplate.format(150), os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'empty.png'))
	for i in range(1, channum + 1):
		name = str(i) + '.png'
		try:
			requests.urlretrieve(icontemplate.format(i), os.path.join(os.path.dirname(sys.argv[0]), 'cache', name))
		except:
			continue
		# logger.debug("No icon for channel:%s"% i)
	logger.debug("Icon download completed.")


def thread_updater():
	while True:
		time.sleep(21600)
		if __version__ < latest_ver:
			logger.info(
				"Your version (%s%s) is out of date, the latest is %s, which has now be downloaded for you into the 'updates' subdirectory." % (
					type, __version__, latest_ver))
			newfilename = ntpath.basename(latestfile)
			if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), 'updates')):
				os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), 'updates'))
			requests.urlretrieve(latestfile, os.path.join(os.path.dirname(sys.argv[0]), 'updates', newfilename))


def find_client(useragent):
	if 'kodi' in useragent.lower():
		return 'kodi'
	elif 'vlc' in useragent.lower():
		return 'vlc'
	elif 'mozilla' in useragent.lower():
		return 'browser'
	elif 'mozilla' in useragent.lower():
		return 'browser'
	elif 'dalvik' in useragent.lower():
		return 'perfectplayer'
	elif 'lavf' in useragent.lower():
		return 'plex'
	elif 'tvheadend' in useragent.lower():
		return 'tvh'
	elif 'apple tv' in useragent.lower():
		return 'atv'
	elif 'smarthub' in useragent.lower():
		return 'samsung'
	elif 'tv' in useragent.lower():
		return 'tv'
	else:
		return 'unk'


############################################################
# EPG
############################################################


def dl_epg(source=1):
	global chan_map, fallback
	# download epg xml
	source = 2 if fallback == True else 1
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml')):
		existing = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml')
		cur_utc_hr = datetime.utcnow().replace(microsecond=0, second=0, minute=0).hour
		target_utc_hr = (cur_utc_hr // 3) * 3
		target_utc_datetime = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=target_utc_hr)
		logger.debug("utc time is: %s,    utc target time is: %s,    file time is: %s" % (
		datetime.utcnow(), target_utc_datetime, datetime.utcfromtimestamp(os.stat(existing).st_mtime)))
		if os.path.isfile(existing) and os.stat(existing).st_mtime > target_utc_datetime.timestamp():
			logger.debug("Skipping download of epg")
			return
	to_process = []
	if OVRXML != '':
		if OVRXML.startswith('http://') or OVRXML.startswith('https://'):
			if OVRXML.endswith('.gz') or OVRXML.endswith('.gz?raw=1'):
				requests.urlretrieve(OVRXML, os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawovrepg.xml.gz'))
				unzipped = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawovrepg.xml.gz')
			else:
				requests.urlretrieve(OVRXML, os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawovrepg.xml'))
				unzipped = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawovrepg.xml')
		else:
			unzipped = OVRXML
		to_process.append([unzipped, "epg.xml", 'ovr'])
		requests.urlretrieve("https://fast-guide.smoothstreams.tv/feed.xml",os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawsports.xml'))
		unzippedsports = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawsports.xml')
		to_process.append([unzippedsports, "sports.xml", 'sstv'])
	elif source == 1:
		logger.info("Downloading epg")
		requests.urlretrieve("https://sstv.fog.pt/epg/xmltv5.xml.gz", os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml.gz'))
		unzipped = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml.gz')
		to_process.append([unzipped, "epg.xml", 'fog'])
		requests.urlretrieve("https://fast-guide.smoothstreams.tv/feed.xml", os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawsports.xml'))
		unzippedsports = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawsports.xml')
		to_process.append([unzippedsports, "sports.xml", 'sstv'])
	else:
		logger.info("Downloading sstv epg")
		requests.urlretrieve("https://fast-guide.smoothstreams.tv/feed.xml", os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml'))
		unzipped = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml')
		to_process.append([unzipped, "epg.xml", 'sstv'])
		to_process.append([unzipped, "sports.xml", 'sstv'])
	for process in to_process:
		# try to categorise the sports events
		if process[0].endswith('.gz'):
			opened = gzip.open(process[0])
		else:
			opened = open(process[0], encoding="UTF-8")
		tree = ET.parse(opened)
		root = tree.getroot()
		changelist = {}
		# remove fogs xmltv channel names for readability in PLex Live
		if process[2] == 'fog':
			for a in tree.iterfind('channel'):
				b = a.find('display-name')
				newname = [chan_map[x].channum for x in range(len(chan_map) + 1) if x != 0 and chan_map[x].epg == a.attrib['id'] and chan_map[x].channame == b.text]
				if len(newname) > 1:
					logger.debug("EPG rename conflict")
				# print(a.attrib['id'], newname)
				else:
					newname = newname[0]
					changelist[a.attrib['id']] = newname
				a.attrib['id'] = newname
		for a in tree.iterfind('programme'):
			if process[2] == 'fog':
				a.attrib['channel'] = changelist[a.attrib['channel']]
			for b in a.findall('title'):
				try:
					c = a.find('category')
					c.text = "Sports"
				except:
					ET.SubElement(a, 'category')
					c = a.find('category')
					c.text = "Sports"
				if 'nba' in b.text.lower() or 'nba' in b.text.lower() or 'ncaam' in b.text.lower():
					c.text = "Basketball"
				elif 'nfl' in b.text.lower() or 'football' in b.text.lower() or 'american football' in b.text.lower() or 'ncaaf' in b.text.lower() or 'cfb' in b.text.lower():
					c.text = "Football"
				elif 'epl' in b.text.lower() or 'efl' in b.text.lower() or 'soccer' in b.text.lower() or 'ucl' in b.text.lower() or 'mls' in b.text.lower() or 'uefa' in b.text.lower() or 'fifa' in b.text.lower() or 'fc' in b.text.lower() or 'la liga' in b.text.lower() or 'serie a' in b.text.lower() or 'wcq' in b.text.lower():
					c.text = "Soccer"
				elif 'rugby' in b.text.lower() or 'nrl' in b.text.lower() or 'afl' in b.text.lower():
					c.text = "Rugby"
				elif 'cricket' in b.text.lower() or 't20' in b.text.lower():
					c.text = "Cricket"
				elif 'tennis' in b.text.lower() or 'squash' in b.text.lower() or 'atp' in b.text.lower():
					c.text = "Tennis/Squash"
				elif 'f1' in b.text.lower() or 'nascar' in b.text.lower() or 'motogp' in b.text.lower() or 'racing' in b.text.lower():
					c.text = "Motor Sport"
				elif 'golf' in b.text.lower() or 'pga' in b.text.lower():
					c.text = "Golf"
				elif 'boxing' in b.text.lower() or 'mma' in b.text.lower() or 'ufc' in b.text.lower() or 'wrestling' in b.text.lower() or 'wwe' in b.text.lower():
					c.text = "Martial Sports"
				elif 'hockey' in b.text.lower() or 'nhl' in b.text.lower() or 'ice hockey' in b.text.lower():
					c.text = "Ice Hockey"
				elif 'baseball' in b.text.lower() or 'mlb' in b.text.lower() or 'beisbol' in b.text.lower() or 'minor league' in b.text.lower():
					c.text = "Baseball"
				# c = a.find('category')
				# if c.text == 'Sports':
				#    print(b.text)
		tree.write(os.path.join(os.path.dirname(sys.argv[0]), 'cache', process[1]))
		logger.debug("writing to %s" % process[1])
		# add xml header to file for Kodi support
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', process[1]), 'r+') as f:
			content = f.read()
			staticinfo = '''<channel id="static_refresh"><display-name lang="en">Static Refresh</display-name><icon src="http://speed.guide.smoothstreams.tv/assets/images/channels/150.png" /></channel><programme channel="static_refresh" start="20170118213000 +0000" stop="20201118233000 +0000"><title lang="us">Press to refresh rtmp channels</title><desc lang="en">Select this channel in order to refresh the RTMP playlist. Only use from the channels list and NOT the guide page. Required every 4hrs.</desc><category lang="us">Other</category><episode-num system="">1</episode-num></programme></tv>'''
			content = content[:-5] + staticinfo
			f.seek(0, 0)
			f.write('<?xml version="1.0" encoding="UTF-8"?>'.rstrip('\r\n') + content)


# started to create epg based off of the json but not needed
def dl_sstv_epg():
	# download epg xml
	# https://guide.smoothstreams.tv/feed-new-full-latest.zip
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'sstv_full.xml')):
		existing = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'sstv_full.xml')
		cur_utc_hr = datetime.utcnow().replace(microsecond=0, second=0, minute=0).hour
		target_utc_hr = (cur_utc_hr // 3) * 3
		target_utc_datetime = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=target_utc_hr)
		print("utc time is: %s,    utc target time is: %s,    file time is: %s" % (
		datetime.utcnow(), target_utc_datetime, datetime.utcfromtimestamp(os.stat(existing).st_mtime)))
		if os.path.isfile(existing) and os.stat(existing).st_mtime > target_utc_datetime.timestamp():
			logger.debug("Skipping download of epg")
			return
	logger.debug("Downloading sstv epg")
	url = "https://guide.smoothstreams.tv/feed-new-full-latest.zip"
	import zipfile
	requests.urlretrieve(url, os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'testepg.zip'))
	archive = zipfile.ZipFile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'testepg.zip'), 'r')
	jsonepg = archive.read('feed-new-full.json')
	epg = json.loads(jsonepg.decode('utf-8'))
	json2xml(epg)


def json2xml(json_obj):
	master = ET.Element('tv')
	mtree = ET.ElementTree(master)
	mroot = mtree.getroot()
	data = json_obj.get('data')
	for i, j in data.items():
		displayname = j['name']
		id = j['number']
		icon = j['img']

		subelement = ET.SubElement(master, 'channel', {'id': id})
		ET.SubElement(subelement, 'icon', {'src': icon})
		ET.SubElement(subelement, 'display-name')

		c = subelement.find('display-name')
		c.text = displayname
		# input
		# '''"851224591": {"name": "SportsCenter With Scott Van Pelt",
		#               "description": "Scott Van Pelt presents the day in sports through his unique perspective with highlights, special guests and his ``One Big Thing'' commentary.",
		#               "time": "1515232800", "runtime": 60, "version": "", "language": "us", "channel": "83",
		#               "category": 0, "parent_id": "0", "quality": "HQLQ", "source": "XMLTV"}'''
		#  sample output from fog
		# <programme channel="I58690.labs.zap2it.com" start="20180105170000 +0000" stop="20180105180000 +0000">
		# <title lang="en">NHL Hockey Central</title>
		# <desc lang="en">News and highlights from around the NHL.</desc>
		# <category lang="en">Ice Hockey</category><
		# episode-num system="">EP02022073.0008</episode-num></programme>
		for event in j['events']:
			program = j['events'][event]
			category = ""
			if 'nba' in program['name'].lower() or 'nba' in program['name'].lower() or 'ncaam' in program[
				'name'].lower():
				category = "Basketball"
			elif 'nfl' in program['name'].lower() or 'football' in program['name'].lower() or 'american football' in \
					program['name'].lower() or 'ncaaf' in program['name'].lower() or 'cfb' in program['name'].lower():
				category = "Football"
			elif 'epl' in program['name'].lower() or 'efl' in program['name'].lower() or 'soccer' in program[
				'name'].lower() or 'ucl' in program['name'].lower() or 'mls' in program['name'].lower() or 'uefa' in \
					program['name'].lower() or 'fifa' in program['name'].lower() or 'fc' in program[
				'name'].lower() or 'la liga' in program['name'].lower() or 'serie a' in program[
				'name'].lower() or 'wcq' in program['name'].lower():
				category = "Soccer"
			elif 'rugby' in program['name'].lower() or 'nrl' in program['name'].lower() or 'afl' in program[
				'name'].lower():
				category = "Rugby"
			elif 'cricket' in program['name'].lower() or 't20' in program['name'].lower():
				category = "Cricket"
			elif 'tennis' in program['name'].lower() or 'squash' in program['name'].lower() or 'atp' in program[
				'name'].lower():
				category = "Tennis/Squash"
			elif 'f1' in program['name'].lower() or 'nascar' in program['name'].lower() or 'motogp' in program[
				'name'].lower() or 'racing' in program['name'].lower():
				category = "Motor Sport"
			elif 'golf' in program['name'].lower() or 'pga' in program['name'].lower():
				category = "Golf"
			elif 'boxing' in program['name'].lower() or 'mma' in program['name'].lower() or 'ufc' in program[
				'name'].lower() or 'wrestling' in program['name'].lower() or 'wwe' in program['name'].lower():
				category = "Martial Sports"
			elif 'hockey' in program['name'].lower() or 'nhl' in program['name'].lower() or 'ice hockey' in program[
				'name'].lower():
				category = "Ice Hockey"
			elif 'baseball' in program['name'].lower() or 'mlb' in program['name'].lower() or 'beisbol' in program[
				'name'].lower() or 'minor league' in program['name'].lower():
				category = "Baseball"
			start = datetime.utcfromtimestamp(int(program['time'])).strftime('%Y%m%d%H%M%S +0000')
			stop = datetime.utcfromtimestamp(int(program['time']) + 60 * int(program['runtime'])).strftime(
				'%Y%m%d%H%M%S +0000')
			subelement = ET.SubElement(master, 'programme', {'id': id, 'start': start, 'stop': stop})
			p_title = ET.SubElement(subelement, 'title', {'lang': program['language']})
			p_title.text = program['name']
			p_desc = ET.SubElement(subelement, 'desc', {'lang': program['language']})
			p_desc.text = program['description']
			p_genre = ET.SubElement(subelement, 'category', {'lang': program['language']})
			p_genre.text = category
	mtree.write(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'sstv_full.xml'))
	return


############################################################
# SSTV
############################################################


def get_auth_token(user, passwd, site):
	if site == 'vaders':
		return
	elif site == 'viewmmasr' or site == 'mmatv':
		baseUrl = 'https://www.mma-tv.net/loginForm.php?'
	else:
		baseUrl = 'https://auth.smoothstreams.tv/hash_api.php?'

	params = {
		"username": user,
		"password": passwd,
		"site": site
	}
	session = req.Session()
	url = baseUrl + urllib.parse.urlencode(params)
	try:
		data = session.post(url, params).json()
	except:
		data = json.loads(requests.urlopen(url).read().decode("utf--8"))
	# old
	# data = json.loads(requests.urlopen('http://auth.SmoothStreams.tv/hash_api.php?username=%s&password=%s&site=%s' % (user,passwd,site)).read().decode("utf-8"))
	if 'hash' not in data or 'valid' not in data:
		logger.error("There was no hash auth token returned from auth.SmoothStreams.tv...")
		return
	else:
		token['hash'] = data['hash']
		token['expires'] = (datetime.now() + timedelta(minutes=data['valid'])).strftime("%Y-%m-%d %H:%M:%S.%f")
		logger.info("Retrieved token %r, expires at %s", token['hash'], token['expires'])
		return


def check_token():
	if SITE == 'vaders':
		return
	# load and check/renew token
	if not token['hash'] or not token['expires']:
		# fetch fresh token
		logger.info("There was no token loaded, retrieving your first token...")
		get_auth_token(USER, PASS, SITE)
		dump_token()
	else:
		# check / renew token
		if datetime.now() > datetime.strptime(token['expires'], "%Y-%m-%d %H:%M:%S.%f"):
			# token is expired, renew
			logger.info("Token has expired, retrieving a new one...")
			get_auth_token(USER, PASS, SITE)
			dump_token()


def build_channel_map():
	chan_map = {}
	logger.debug("Loading channel list")
	url = 'https://sstv.fog.pt/epg/channels.json'
	jsonChanList = json.loads(requests.urlopen(url).read().decode("utf-8"))

	for item in jsonChanList:
		retVal = channelinfo()
		# print(item)
		oChannel = jsonChanList[item]
		retVal.channum = oChannel["channum"]
		channel = int(oChannel["channum"])
		retVal.channame = oChannel["channame"].replace(format(channel, "02") + " - ", "").strip()
		if retVal.channame == 'Empty':
			retVal.channame = retVal.channum
		retVal.epg = oChannel["xmltvid"]
		chan_map[channel] = {}
		chan_map[channel] = retVal

	logger.debug("Built channel map with %d channels", len(chan_map))
	return chan_map


def build_channel_map_sstv():
	chan_map = {}
	logger.debug("Loading channel list (fallback)")
	url = 'https://speed.guide.smoothstreams.tv/feed-new.json'
	jsonChanList = json.loads(requests.urlopen(url).read().decode("utf-8"))
	jsonEPG = jsonChanList['data']

	for item in jsonEPG:
		retVal = channelinfo()
		# print(item)
		oChannel = jsonEPG[item]
		retVal.channum = oChannel["number"]
		channel = int(oChannel["number"])
		retVal.channame = oChannel["name"].replace(format(channel, "02") + " - ", "").strip()
		if retVal.channame == 'Empty':
			retVal.channame = retVal.channum
		retVal.epg = oChannel["number"]
		chan_map[channel] = {}
		chan_map[channel] = retVal

	logger.debug("Built channel map with %d channels", len(chan_map))
	return chan_map


def build_playlist(host):
	# standard dynamic playlist
	global chan_map

	# build playlist using the data we have
	new_playlist = "#EXTM3U x-tvg-url='%s/epg.xml'\n" % urljoin(host, SERVER_PATH)
	for pos in range(1, len(chan_map) + 1):
		# build channel url
		url = "{0}/playlist.m3u8?ch={1}&strm={2}&qual={3}"
		vaders_url = "http://vaders.tv/live/{0}/{1}/{2}.{3}"

		if SITE == 'vaders':
			strm = 'ts' if STRM == 'mpegts' else 'm3u8'
			channel_url = vaders_url.format('vsmystreams_' + USER,PASS, vaders_channels[str(pos)], strm)
		else:
			urlformatted = url.format(SERVER_PATH, chan_map[pos].channum, STRM, QUAL)
			channel_url = urljoin(host, urlformatted)
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, host, SERVER_PATH, chan_map[pos].channum,
				chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % channel_url

		except:
			logger.exception("Exception while updating playlist: ")
	logger.info("Built Dynamic playlist")

	return new_playlist


def build_static_playlist():
	global chan_map
	# build playlist using the data we have
	new_playlist = "#EXTM3U x-tvg-url='%s/epg.xml'\n" % urljoin(SERVER_HOST, SERVER_PATH)
	for pos in range(1, len(chan_map) + 1):
		# build channel url

		template = '{0}://{1}.smoothstreams.tv:{2}/{3}/ch{4}q{5}.stream{6}?wmsAuthSign={7}'
		urlformatted = template.format('https' if STRM == 'hls' else 'rtmp', SRVR, '443' if STRM == 'hls' else '3625',
									   SITE, "{:02}".format(pos), QUAL if pos <= 60 else '1',
									   '/playlist.m3u8' if STRM == 'hls' else '', token['hash'])
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH, chan_map[pos].channum,
				chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % urlformatted
		except:
			logger.exception("Exception while updating static playlist: ")
	logger.info("Built static playlist")
	return new_playlist


def build_test_playlist(hosts):
	# build playlist using the data we have
	new_playlist = "#EXTM3U x-tvg-url='%s/epg.xml'\n" % urljoin(SERVER_HOST, SERVER_PATH)
	template = '{0}://{1}.smoothstreams.tv:{2}/{3}/ch{4}q{5}.stream{6}?wmsAuthSign={7}'
	url = "{0}/sstv/playlist.m3u8?ch=1&strm=hls&qual=1&type={1}"
	# build playlist entry
	new_playlist += '#EXTINF:-1 tvg-id="1" tvg-name="Static HLS" channel-id="1","Static HLS"\n'
	new_playlist += '%s\n' % template.format('https', 'dnaw1', '443', SITE, "01", 1, '/playlist.m3u8', token['hash'])
	new_playlist += '#EXTINF:-1 tvg-id="2" tvg-name="Static RTMP" channel-id="2","Static RTMP"\n'
	new_playlist += '%s\n' % template.format('rtmp', 'dnaw1', '3625', SITE, "01", 1, '', token['hash'])
	count = 3
	for host in hosts:
		new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="Redirect" channel-id="%s","Redirect"\n' % (count, count)
		new_playlist += '%s\n' % url.format(host, '1')
		count += 1
		new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="File" channel-id="%s","File"\n' % (count, count)
		new_playlist += '%s\n' % url.format(host, '2')
		count += 1
		new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="Variable" channel-id="%s","Variable"\n' % (count, count)
		new_playlist += '%s\n' % url.format(host, '3')
		count += 1
		new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="URL" channel-id="%s","URL"\n' % (count, count)
		new_playlist += '%s\n' % url.format(host, '4')
		count += 1

	logger.info("Built static playlist")
	return new_playlist


def thread_playlist():
	global playlist

	while True:
		time.sleep(86400)
		logger.info("Updating playlist...")
		try:
			tmp_playlist = build_playlist(SERVER_HOST)
			playlist = tmp_playlist
			logger.info("Updated playlist!")
		except:
			logger.exception("Exception while updating playlist: ")


def create_channel_playlist(sanitized_channel, qual, strm, hash):
	rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
	hlsTemplate = 'https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}=='
	hls_url = hlsTemplate.format(SRVR, SITE, sanitized_channel, qual, hash)
	rtmp_url = rtmpTemplate.format(SRVR, SITE, sanitized_channel, qual, hash)
	file = requests.urlopen(hls_url).read().decode("utf-8")
	if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'playlist.m3u8')):
		f = open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'playlist.m3u8'), 'w')
		f.close()
	if strm == 'hls':
		# Used to support HLS HTTPS requests
		template = 'https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/chunks'
		file = file.replace('chunks', template.format(SRVR, SITE, sanitized_channel, qual))
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'playlist.m3u8'), 'r+') as f:
			f.write(file)
		return file
	else:
		# not used currently
		template = 'http://{0}.smoothstreams.tv:9100/{1}/ch{2}q{3}.stream/chunks'
		file = '#EXTM3U\n#EXTINF:' + file[43:110] + "\n" + rtmp_url
		# with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'playlist.m3u8'), 'r+') as f:
		#    f.write(file)
		return rtmp_url


############################################################
# m3u8 merger
############################################################

def obtain_m3u8():
	formatted_m3u8 = ''
	url = EXTM3URL
	name = EXTM3UNAME
	file = EXTM3UFILE
	if url != '':
		logger.debug("extra m3u8 url")
		inputm3u8 = requests.urlopen(url).read().decode('utf-8')
		inputm3u8 = inputm3u8.split("\n")[1:]
	elif file != '':
		logger.debug("extra m3u8 file")
		f = open(file, 'r')
		inputm3u8 = f.readlines()
		inputm3u8 = inputm3u8[1:]
		inputm3u8 = [x.strip("\n") for x in inputm3u8]
	else:
		logger.debug("extra m3u8 nothing")
		return formatted_m3u8

	for i in range(len(inputm3u8)):
		if inputm3u8[i] != "" or inputm3u8[i] != "\n":
			try:
				if inputm3u8[i].startswith("#"):
					grouper = inputm3u8[i]
					grouper = grouper.split(',')
					grouper = grouper[0] + ' group-title="%s"' % (name) + "," + grouper[1]
					if i != 0:
						formatted_m3u8 += "\n"
					formatted_m3u8 += grouper
				else:
					formatted_m3u8 += "\n" + inputm3u8[i]
			except:
				logger.debug("skipped:", inputm3u8[i])
	return formatted_m3u8


def xmltv_merger():
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'combined.xml')):
		existing = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'combined.xml')
		cur_utc_hr = datetime.utcnow().replace(microsecond=0, second=0, minute=0).hour
		target_utc_hr = (cur_utc_hr // 3) * 3
		target_utc_datetime = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=target_utc_hr)
		logger.debug("utc time is: %s,    utc target time is: %s,    file time is: %s" % (
		datetime.utcnow(), target_utc_datetime, datetime.utcfromtimestamp(os.stat(existing).st_mtime)))
		if os.path.isfile(existing) and os.stat(existing).st_mtime > target_utc_datetime.timestamp():
			logger.debug("Skipping download of epg")
			return
	requests.urlretrieve(EXTXMLURL, os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'extra.xml'))
	xml_files = ['./cache/epg.xml', './cache/extra.xml']
	master = ET.Element('tv')
	mtree = ET.ElementTree(master)
	mroot = mtree.getroot()
	for file in xml_files:
		tree = ET.parse(file)
		for channel in tree.iter('channel'):
			mroot.append(channel)
	for file in xml_files:
		tree = ET.parse(file)
		for programme in tree.iter('programme'):
			mroot.append(programme)
		# if xml_element_tree is not None:
		# 	print(ET.tostring(xml_element_tree))
	mtree.write(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'combined.xml'))
	with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'combined.xml'), 'r+') as f:
		content = f.read()
		f.seek(0, 0)
		f.write('<?xml version="1.0" encoding="UTF-8"?>'.rstrip('\r\n') + content)
	return


############################################################
# TVHeadend
############################################################

def build_tvh_playlist():
	global chan_map

	# build playlist using the data we have
	new_playlist = "#EXTM3U\n"
	for pos in range(1, len(chan_map) + 1):
		# build channel url
		template = "{0}/{1}/auto/v{2}"
		channel_url = template.format(SERVER_HOST, SERVER_PATH, chan_map[pos].channum)
		name = str(pos) + " " + chan_map[pos].channame
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvh-chnum="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channum, name, SERVER_HOST, SERVER_PATH, chan_map[pos].channum,
				chan_map[pos].channum, name)
			new_playlist += '%s\n' % channel_url

		except:
			logger.exception("Exception while updating playlist: ")
	logger.info("Built TVH playlist")

	return new_playlist


def get_tvh_channels():
	url = 'HTTP://%s:9981/api/channel/grid?start=0&limit=999999' % TVHURL
	try:
		r = req.get(url, auth=req.auth.HTTPBasicAuth(TVHUSER, TVHPASS)).text
		data = json.loads(r)
		return (data['entries'])
	except:
		print('An error occured')


############################################################
# PLEX Live
############################################################





def discover():
	discoverData = {
		'FriendlyName': 'SSTVProxy',
		'Manufacturer': 'Silicondust',
		'ModelNumber': 'HDTC-2US',
		'FirmwareName': 'hdhomeruntc_atsc',
		'TunerCount': 6,
		'FirmwareVersion': '20150826',
		'DeviceID': '12345678',
		'DeviceAuth': 'test1234',
		'BaseURL': SERVER_HOST + "/" + SERVER_PATH,
		'LineupURL': '%s/lineup.json' % urljoin(SERVER_HOST, SERVER_PATH)
	}
	return jsonify(discoverData)


def tvh_discover():
	tvhdiscoverData = {
		'FriendlyName': 'SSTVProxy',
		'Manufacturer': 'Silicondust',
		'ModelNumber': 'HDTC-2US',
		'FirmwareName': 'hdhomeruntc_atsc',
		'TunerCount': 6,
		'FirmwareVersion': '20150826',
		'DeviceID': '12345678',
		'DeviceAuth': 'test1234',
		'BaseURL': SERVER_HOST + "/tvh",
		'LineupURL': '%s/lineup.json' % (SERVER_HOST + "/tvh")
	}
	return jsonify(tvhdiscoverData)


def status():
	return jsonify({
		'ScanInProgress': 0,
		'ScanPossible': 1,
		'Source': "Cable",
		'SourceList': ['Cable']
	})


def m3u8_plex(lineup, inputm3u8):
	for i in range(len(inputm3u8)):
		if inputm3u8[i] != "" or inputm3u8[i] != "\n":
			try:
				if inputm3u8[i].startswith("#"):
					grouper = inputm3u8[i]
					grouper = grouper.split(',')
					name = grouper[1]
					lineup.append({'GuideNumber': str(len(lineup) + 1),
								   'GuideName': name,
								   'URL': 'empty'
								   })
				elif inputm3u8[i].startswith("rtmp") or inputm3u8[i].startswith("http"):
					template = "{0}/{1}/auto/v{2}?url={3}"
					url = template.format(SERVER_HOST, SERVER_PATH, str(len(lineup)), inputm3u8[i])
					lineup[-1]['URL'] = url

			except:
				logger.debug("skipped:", inputm3u8[i])
	return lineup


def lineup(chan_map):
	lineup = []

	for c in range(1, len(chan_map) + 1):
		template = "{0}/{1}/auto/v{2}"
		url = template.format(SERVER_HOST, SERVER_PATH, chan_map[c].channum)
		lineup.append({'GuideNumber': str(chan_map[c].channum),
					   'GuideName': chan_map[c].channame,
					   'URL': url
					   })
	formatted_m3u8 = ''
	if EXTM3URL != '':
		logger.debug("extra m3u8 url")
		inputm3u8 = requests.urlopen(EXTM3URL).read().decode('utf-8')
		inputm3u8 = inputm3u8.split("\n")[1:]
		return jsonify(m3u8_plex(lineup, inputm3u8))
	elif EXTM3UFILE != '':
		logger.debug("extra m3u8 file")
		f = open(EXTM3UFILE, 'r')
		inputm3u8 = f.readlines()
		inputm3u8 = inputm3u8[1:]
		inputm3u8 = [x.strip("\n") for x in inputm3u8]
		return jsonify(m3u8_plex(lineup, inputm3u8))
	return jsonify(lineup)


def tvh_lineup():
	lineup = []
	for c in get_tvh_channels():
		if c['enabled']:
			url = 'http://%s:%s@%s:9981/stream/channel/%s?profile=%s&weight=%s' % (
			TVHUSER, TVHPASS, TVHURL, c['uuid'], tvhstreamProfile, int(tvhWeight))
			lineup.append({'GuideNumber': str(c['number']),
						   'GuideName': c['name'],
						   'URL': url
						   })
	return jsonify(lineup)


def lineup_post():
	return ''


def device():
	discoverData = {
		'FriendlyName': 'SSTVProxy',
		'Manufacturer': 'Silicondust',
		'ModelNumber': 'HDTC-2US',
		'FirmwareName': 'hdhomeruntc_atsc',
		'TunerCount': 6,
		'FirmwareVersion': '20150826',
		'DeviceID': '12345678',
		'DeviceAuth': 'test1234',
		'BaseURL': SERVER_HOST + "/" + SERVER_PATH,
		'LineupURL': '%s/lineup.json' % urljoin(SERVER_HOST, SERVER_PATH)
	}
	return render_template('device.xml', data=discoverData), {'Content-Type': 'application/xml'}


def tvh_device():
	tvhdiscoverData = {
		'FriendlyName': 'SSTVProxy',
		'Manufacturer': 'Silicondust',
		'ModelNumber': 'HDTC-2US',
		'FirmwareName': 'hdhomeruntc_atsc',
		'TunerCount': 6,
		'FirmwareVersion': '20150826',
		'DeviceID': '12345678',
		'DeviceAuth': 'test1234',
		'BaseURL': SERVER_HOST + "/tvh",
		'LineupURL': '%s/lineup.json' % (SERVER_HOST + "/tvh")
	}
	return render_template('device.xml', data=tvhdiscoverData), {'Content-Type': 'application/xml'}


# PLEX DVR EPG from here
# Where the script looks for an EPG database
try:
	epgpath = os.path.join(
		os.path.join(os.path.expanduser("~"), "AppData", "Local", "Plex Media Server", "Plug-in Support", "Databases"))
	dbpat = [[item for item in files if
			  item.endswith(".db") and item.startswith("tv.plex.providers.epg.xmltv-") and "loading" not in item] for
			 root, dirs, files in os.walk(epgpath)][0]
except:
	dbpat = []


def create_list(dbname, epgsummaries=False, epggenres=False, epgorig=False):
	with sqlite3.connect(dbname) as epgconn, open("./cache/guide.html", "w") as html:

		html.write("""<html>
		<head>
		<meta charset="UTF-8">
		%s
		</head>
		<body>\n""" % (style,))

		epgconn.row_factory = sqlite3.Row
		c = epgconn.cursor()

		# type 1 movie
		# type 2 show, 3 season, 4 episode

		query = "SELECT DISTINCT tags.tag as channel " \
				"FROM media_items AS bc " \
				"JOIN metadata_items AS it ON bc.metadata_item_id = it.id " \
				"JOIN tags ON tags.id = bc.channel_id " \
				"ORDER BY bc.channel_id "

		html.write("<h1>Channel Index</h1>")

		channelmap = {}
		chanindex = 0
		for row in c.execute(query):
			chanindex += 1
			channel = row["channel"]
			channelmap[channel] = chanindex
			html.write("<span class=\"channellink\"><a href=\"#%s\">%s</a></span>" %
					   (chanindex, channel))

		query = "SELECT tags.tag as channel, " \
				"bc.begins_at, bc.ends_at, " \
				"it.title, it.user_thumb_url, it.year, it.summary, it.extra_data as subscribed, " \
				"it.\"index\" as episode, it.summary, it.tags_genre as itgenre, " \
				"it.originally_available_at as origdate, " \
				"seas.\"index\" AS season, " \
				"show.title as showtitle, show.tags_genre as showgenre " \
				"FROM media_items AS bc " \
				"JOIN metadata_items AS it ON bc.metadata_item_id = it.id " \
				"JOIN tags ON tags.id = bc.channel_id " \
				"LEFT JOIN metadata_items AS seas ON seas.id = it.parent_id " \
				"LEFT JOIN metadata_items AS show ON show.id = seas.parent_id " \
				"WHERE it.metadata_type IN (1,4) " \
				"ORDER BY bc.channel_id, bc.begins_at "

		prevChannel = None
		prevEnd = None
		prevDate = None

		for row in c.execute(query):

			channel = row["channel"]
			if channel != prevChannel:
				html.write("<h1><a name=\"%s\"></a>Channel: %s</h1>" % (channelmap[channel], channel))
				prevChannel = channel
				prevEnd = None
				prevDate = None

			date = row["begins_at"][:10]
			if date != prevDate:
				html.write("<h2>Date: %s</h2>" % date)
				prevDate = date

			start = row["begins_at"][:-3]
			end = row["ends_at"][:-3]
			shortend = end[11:] if start[:11] == end[:11] else end

			if prevEnd is not None and start != prevEnd:
				html.write("<p class=\"gap\">Gap between %s and %s\n" % (start, shortend))

			if row["season"]:
				# It's an episode
				ep = ("%02d" % row["episode"]) if row["episode"] >= 0 else "??"
				titlestr = ("&ndash; <span class=\"episodetitle\">" + row["title"] + "</span>" if row["title"] else "")
				html.write("<p>%s &ndash; %s: <b>%s</b> S%02dE%s %s\n" %
						   (start, shortend, row["showtitle"], row["season"], ep,
							titlestr))
			else:
				# It's a movie
				html.write("<p>%s &ndash; %s: <b>%s</b>\n" %  # (%d)\n" %
						   (start, end, row["title"]))  # , row["year"]))

			# Doesn't mean *this* broadcast will be recorded!
			if row["subscribed"]:
				html.write(" <span class=\"recorded\">*** To be recorded some time ***</span>")

			if epgorig:
				html.write("<p class=\"origdate\">Original air date: %s</p>" % row["origdate"][:10])

			if epggenres:
				if row["itgenre"]:
					html.write("<p class=\"genre\">Genre: %s</p>" % row["itgenre"])
				if row["showgenre"]:
					html.write("<p class=\"genre\">Genre: %s</p>" % row["showgenre"])

			if epgsummaries:
				html.write("<p class=\"summary\">%s</p>\n" % row["summary"])
			prevEnd = end

		html.write("</body></html>\n")


def epgguide(epgsummaries=False, epggenres=False, epgorig=False):
	dbs = glob.glob(dbpat)

	if len(dbs) == 0:
		logger.debug("Found no database matching %s" % dbpat)
	elif len(dbs) > 1:
		logger.debug("Found multiple databases matching %s" % dbpat)
	else:
		dbfile = dbs[0]
		if not os.access(dbfile, os.W_OK):
			logger.exception("Database file not writable (required for queries): %s" % dbfile)
		else:
			create_list(dbfile, epgsummaries, epggenres, epgorig)


# PLEX DVR EPG Ends


############################################################
# PLEX Discovery
############################################################

HDHOMERUN_DISCOVER_UDP_PORT = 65001
HDHOMERUN_CONTROL_TCP_PORT = 65001
HDHOMERUN_MAX_PACKET_SIZE = 1460
HDHOMERUN_MAX_PAYLOAD_SIZE = 1452

HDHOMERUN_TYPE_DISCOVER_REQ = 0x0002
HDHOMERUN_TYPE_DISCOVER_RPY = 0x0003
HDHOMERUN_TYPE_GETSET_REQ = 0x0004
HDHOMERUN_TYPE_GETSET_RPY = 0x0005
HDHOMERUN_TAG_DEVICE_TYPE = 0x01
HDHOMERUN_TAG_DEVICE_ID = 0x02
HDHOMERUN_TAG_GETSET_NAME = 0x03
HDHOMERUN_TAG_GETSET_VALUE = 0x04
HDHOMERUN_TAG_GETSET_LOCKKEY = 0x15
HDHOMERUN_TAG_ERROR_MESSAGE = 0x05
HDHOMERUN_TAG_TUNER_COUNT = 0x10
HDHOMERUN_TAG_DEVICE_AUTH_BIN = 0x29
HDHOMERUN_TAG_BASE_URL = 0x2A
HDHOMERUN_TAG_DEVICE_AUTH_STR = 0x2B

HDHOMERUN_DEVICE_TYPE_WILDCARD = 0xFFFFFFFF
HDHOMERUN_DEVICE_TYPE_TUNER = 0x00000001
HDHOMERUN_DEVICE_ID_WILDCARD = 0xFFFFFFFF

ignorelist = [
	'127.0.0.1']  # the tvheadend ip address(es), tvheadend crashes when it discovers the tvhproxy (TODO: Fix this)


def retrieveTypeAndPayload(packet):
	header = packet[:4]
	checksum = packet[-4:]
	payload = packet[4:-4]

	packetType, payloadLength = struct.unpack('>HH', header)
	if payloadLength != len(payload):
		logger.debug('Bad packet payload length')
		return False

	if checksum != struct.pack('>I', cksum(header + payload)):
		logger.debug('Bad checksum')
		return False

	return (packetType, payload)


def createPacket(packetType, payload):
	header = struct.pack('>HH', packetType, len(payload))
	data = header + payload
	checksum = cksum(data)
	packet = data + struct.pack('>I', checksum)

	return packet


def processPacket(packet, client, logPrefix=''):
	packetType, requestPayload = retrieveTypeAndPayload(packet)

	if packetType == HDHOMERUN_TYPE_DISCOVER_REQ:
		logger.debug('Discovery request received from ' + client[0])
		responsePayload = struct.pack('>BBI', HDHOMERUN_TAG_DEVICE_TYPE, 0x04,
									  HDHOMERUN_DEVICE_TYPE_TUNER)  # Device Type Filter (tuner)
		responsePayload += struct.pack('>BBI', HDHOMERUN_TAG_DEVICE_ID, 0x04,
									   int('12345678', 16))  # Device ID Filter (any)
		responsePayload += struct.pack('>BB', HDHOMERUN_TAG_GETSET_NAME, len(SERVER_HOST)) + str.encode(
			SERVER_HOST)  # Device ID Filter (any)
		responsePayload += struct.pack('>BBB', HDHOMERUN_TAG_TUNER_COUNT, 0x01, 6)  # Device ID Filter (any)

		return createPacket(HDHOMERUN_TYPE_DISCOVER_RPY, responsePayload)

	# TODO: Implement request types
	if packetType == HDHOMERUN_TYPE_GETSET_REQ:
		logger.debug('Get set request received from ' + client[0])
		getSetName = None
		getSetValue = None
		payloadIO = StringIO(requestPayload)
		while True:
			header = payloadIO.read(2)
			if not header: break
			tag, length = struct.unpack('>BB', header)
			# TODO: If the length is larger than 127 the following bit is also needed to determine length
			if length > 127:
				logger.debug(
					'Unable to determine tag length, the correct way to determine a length larger than 127 must still be implemented.')
				return False
			# TODO: Implement other tags
			if tag == HDHOMERUN_TAG_GETSET_NAME:
				getSetName = struct.unpack('>{0}'.format(length), payloadIO.read(length))[0]
			if tag == HDHOMERUN_TAG_GETSET_VALUE:
				getSetValue = struct.unpack('>{0}'.format(length), payloadIO.read(length))[0]

		if getSetName is None:
			return False
		else:
			responsePayload = struct.pack('>BB{0}'.format(len(getSetName)), HDHOMERUN_TAG_GETSET_NAME, len(getSetName),
										  getSetName)

			if getSetValue is not None:
				responsePayload += struct.pack('>BB{0}'.format(len(getSetValue)), HDHOMERUN_TAG_GETSET_VALUE,
											   len(getSetValue), getSetValue)

			return createPacket(HDHOMERUN_TYPE_GETSET_RPY, responsePayload)

	return False


def tcpServer():
	logger.info('Starting tcp server')
	controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	controlSocket.bind((LISTEN_IP, HDHOMERUN_CONTROL_TCP_PORT))
	controlSocket.listen(1)

	logger.info('Listening...')
	try:
		while True:
			connection, client = controlSocket.accept()
			try:
				packet = connection.recv(HDHOMERUN_MAX_PACKET_SIZE)
				if not packet:
					logger.debug('No packet received')
					break
				if client[0] not in ignorelist:
					responsePacket = processPacket(packet, client)
					if responsePacket:
						logger.debug('Sending control reply over tcp')
						connection.send(responsePacket)
					else:
						logger.debug('No known control request received, nothing to send to client')
				else:
					logger.debug('Ignoring tcp client %s' % client[0])
			finally:
				connection.close()
	except:
		logger.debug('Exception occured')

	logger.info('Stopping tcp server')
	controlSocket.close()


def udpServer():
	logger.info('Starting udp server')
	discoverySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	discoverySocket.bind(('0.0.0.0', HDHOMERUN_DISCOVER_UDP_PORT))
	logger.info('Listening...')
	while True:
		packet, client = discoverySocket.recvfrom(HDHOMERUN_MAX_PACKET_SIZE)
		if not packet:
			logger.debug('No packet received')
			break
		if client[0] not in ignorelist:
			responsePacket = processPacket(packet, client)
			if responsePacket:
				logger.debug('Sending discovery reply over udp')
				discoverySocket.sendto(responsePacket, client)
			else:
				logger.debug('No discovery request received, nothing to send to client')
		else:
			logger.debug('Ignoring udp client %s' % client[0])
	logger.info('Stopping udp server')
	discoverySocket.close()


############################################################
# Kodi
############################################################


def build_kodi_playlist():
	# kodi playlist contains two copies of channels, first is dynmaic HLS and the second is static rtmp
	global chan_map
	# build playlist using the data we have
	new_playlist = "#EXTM3U x-tvg-url='%s/epg.xml'\n" % urljoin(SERVER_HOST, SERVER_PATH)
	for pos in range(1, len(chan_map) + 1):
		# build channel url
		url = "{0}/playlist.m3u8?ch={1}&strm={2}&qual={3}&client=kodi"
		rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
		urlformatted = url.format(SERVER_PATH, chan_map[pos].channum, 'hls', QUAL)
		channel_url = urljoin(SERVER_HOST, urlformatted)
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s" group-title="Dynamic",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH, chan_map[pos].channum,
				chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % channel_url
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s" group-title="Static RTMP",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH, chan_map[pos].channum,
				chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % rtmpTemplate.format(SRVR, SITE, "{:02}".format(pos), QUAL if pos <= 60 else '1',
														 token['hash'])
		except:
			logger.exception("Exception while updating kodi playlist: ")
	new_playlist += '#EXTINF:-1 tvg-id="static_refresh" tvg-name="Static Refresh" tvg-logo="%s/%s/empty.png" channel-id="0" group-title="Static RTMP",Static Refresh\n' % (
		SERVER_HOST, SERVER_PATH)
	new_playlist += '%s/%s/refresh.m3u8\n' % (SERVER_HOST, SERVER_PATH)
	logger.info("Built Kodi playlist")

	# if ADDONPATH and os.path.isdir(ADDONPATH):
	# 	#lazy install, low priority tbh
	# 	tree = ET.parse(os.path.join(ADDONPATH, 'settings.xml'))
	# 	root = tree.getroot()
	# 	for child in root:
	# 		if child.attrib['id'] == 'epgUrl':
	# 			child.attrib['value'] = '%s/%s/epg.xml' % (SERVER_HOST, SERVER_PATH)
	# 		elif child.attrib['id'] == 'm3uUrl':
	# 			child.attrib['value'] = '%s/%s/kodi.m3u8' % (SERVER_HOST, SERVER_PATH)
	# 		elif child.attrib['id'] == 'epgPathType':
	# 			child.attrib['value'] = '1'
	# 		elif child.attrib['id'] == 'm3uPathType':
	# 			child.attrib['value'] = '1'
	# 	tree.write(os.path.join(ADDONPATH, 'settings.xml'))
	return new_playlist


def rescan_channels():
	credentials = str.encode(KODIUSER + ':' + KODIPASS)
	encoded_credentials = base64.b64encode(credentials)
	authorization = b'Basic ' + encoded_credentials
	apiheaders = {'Content-Type': 'application/json', 'Authorization': authorization}
	apidata = {"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled",
			   "params": {"addonid": "pvr.iptvsimple", "enabled": "toggle"}, "id": 1}
	apiurl = 'http://%s:%s/jsonrpc' % (request.environ.get('REMOTE_ADDR'), KODIPORT)
	json_data = json.dumps(apidata)
	post_data = json_data.encode('utf-8')
	apirequest = requests.Request(apiurl, post_data, apiheaders)
	# has to happen twice to toggle off then back on
	result = requests.urlopen(apirequest)
	result = requests.urlopen(apirequest)
	logger.info("Forcing Kodi to rescan, result:%s " % result.read())


############################################################
# Html
############################################################


# Change this to change the style of the web page generated
style = """
<style type="text/css">
	body { max-width: 30em; background: white url("https://guide.smoothstreams.tv/assets/images/channels/150.png") no-repeat fixed center center; background-size: 500px 500px; color: black; }
	h1 { color: white; background-color: black; padding: 0.5ex }
	h2 { color: white; background-color: #404040; padding: 0.3ex }
	.gap { color: darkred; }
	.recorded { color: green; font-weight: bold; }
	.summary { font-size: 85%%; color: #505050; margin-left: 4em; }
	.genre { margin-left: 4em; }
	.origdate { margin-left: 4em; }
	.episodetitle { font-style: italic; font-weight: bold }
	.channellink { display: inline-block; width: 10em; }
	.channellink A { color: black; text-decoration: none; }
	.container {display: table; width: 100%;}
	.left-half {position: absolute;  left: 0px;  width: 50%;}
	.right-half {position: absolute;  right: 0px;  width: 50%;}
</style>
"""


def create_menu():
	with open("./cache/settings.html", "w") as html:
		html.write("""<html>
		<head>
		<meta charset="UTF-8">
		%s
		<title>YAP</title>
		</head>
		<body>\n""" % (style,))
		html.write('<section class="container"><div class="left-half">')
		html.write("<h1>YAP Settings</h1>")
		html.write('<form action="%s/%s/handle_data" method="post">' % (SERVER_HOST, SERVER_PATH))

		channelmap = {}
		chanindex = 0
		list = ["Username", "Password", "Quality", "Stream", "Server", "Service", "IP", "Port", "Kodiport",
				"ExternalIP", "ExternalPort"]
		html.write('<table width="300" border="2">')
		for setting in list:
			if setting.lower() == 'service':
				html.write('<tr><td>Service:</td><td><select name="Service" size="1">')
				for option in providerList:
					html.write('<option value="%s"%s>%s</option>' % (
					option[0], ' selected' if SITE == option[1] else "", option[0]))
				html.write('</select></td></tr>')
			elif setting.lower() == 'server':
				html.write('<tr><td>Server:</td><td><select name="Server" size="1">')
				for option in serverList:
					html.write('<option value="%s"%s>%s</option>' % (
					option[0], ' selected' if SRVR == option[1] else "", option[0]))
				html.write('</select></td></tr>')
			elif setting.lower() == 'stream':
				html.write('<tr><td>Stream:</td><td><select name="Stream" size="1">')
				for option in streamtype:
					html.write(
						'<option value="%s"%s>%s</option>' % (option, ' selected' if STRM == option else "", option))
				html.write('</select></td></tr>')
			elif setting.lower() == 'quality':
				html.write('<tr><td>Quality:</td><td><select name="Quality" size="1">')
				for option in qualityList:
					html.write('<option value="%s"%s>%s</option>' % (
					option[0], ' selected' if QUAL == option[1] else "", option[0]))
				html.write('</select></td></tr>')
			elif setting.lower() == 'password':
				html.write('<tr><td>%s:</td><td><input name="%s" type="Password" value="%s"></td></tr>' % (
				setting, setting, PASS))
			else:
				val = "Unknown"
				if setting == "Username":
					val = USER
				elif setting == "IP":
					val = LISTEN_IP
				elif setting == "Port":
					val = LISTEN_PORT
				elif setting == "Kodiport":
					val = KODIPORT
				elif setting == "ExternalIP":
					val = EXTIP
				elif setting == "ExternalPort":
					val = EXTPORT
				html.write(
					'<tr><td>%s:</td><td><input name="%s" type="text" value="%s"></td></tr>' % (setting, setting, val))
		html.write('</table>')
		html.write('<input type="submit"  value="Submit">')
		html.write('</form>')
		html.write("<p>You are running version (%s %s), the latest is %s</p>" % (type, __version__, latest_ver))
		html.write("</br><p>Restarts can take a while, it is not immediate.</p>")
		html.write('<form action="%s/%s/handle_data" method="post">' % (SERVER_HOST, SERVER_PATH))
		html.write('<input type="hidden" name="restart"  value="1">')
		html.write('<input type="submit"  value="Restart">')
		html.write('</form>')
		html.write('<form action="%s/%s/handle_data" method="post">' % (SERVER_HOST, SERVER_PATH))
		html.write('<input type="hidden" name="restart"  value="2">')
		html.write('<input type="submit"  value="Update + Restart">')
		html.write('</form>')
		html.write('<form action="%s/%s/handle_data" method="post">' % (SERVER_HOST, SERVER_PATH))
		html.write('<input type="hidden" name="restart"  value="3">')
		html.write('<input type="submit"  value="Update(Dev Branch) + Restart">')
		html.write('</form>')
		html.write('<p>&nbsp;</p>')
		html.write('<p>&nbsp;</p>')
		html.write('<p>&nbsp;</p>')
		html.write('<p>&nbsp;</p>')
		html.write('<p>Donations: PayPal to vorghahn.sstv@gmail.com  or BTC - 19qvdk7JYgFruie73jE4VvW7ZJBv8uGtFb</p>')
		html.write('</div><div class="right-half"><h1>YAP Outputs</h1>')

		html.write("<table><tr><td rowspan='2'>Standard Outputs</td><td>m3u8 - %s/playlist.m3u8</td></tr>" % urljoin(
			SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>EPG - %s/epg.xml</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write(
			"<tr><td>Sports EPG (Alternative)</td><td>%s/sports.xml</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write(
			"<tr><td>Kodi RTMP supported</td><td>m3u8 - %s/kodi.m3u8</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")

		html.write("<tr><td rowspan='2'>Plex Live<sup>1</sup></td><td>Tuner - %s</td></tr>" % urljoin(SERVER_HOST,
																									  SERVER_PATH))
		html.write("<tr><td>EPG - %s/epg.xml</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write("<tr><td>TVHeadend<sup>1</sup></td><td>%s/tvh.m3u8</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write(
			"<tr><td rowspan='2'>Remote Internet access<sup>2</sup></td><td>m3u8 - %s/external.m3u8</td></tr>" % urljoin(
				EXT_HOST, SERVER_PATH))
		html.write("<tr><td>EPG - %s/epg.xml</td></tr>" % urljoin(EXT_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")

		html.write(
			"<tr><td rowspan='2'>Combined Outputs<sup>2</sup></td><td>m3u8 - %s/combined.m3u8</td></tr>" % urljoin(
				SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>epg - %s/combined.xml</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")

		html.write(
			"<tr><td>Static Playlist</td><td>m3u8 - %s/static.m3u8</td></tr>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")

		html.write(
			"<tr><td rowspan='2'>TVHProxy<sup>3</sup></td><td>Tuner - %s</td></tr>" % urljoin(SERVER_HOST, 'tvh'))
		html.write("<tr><td>EPG - http://%s:9981/xmltv/channels</td></tr>" % TVHURL)
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write("<tr><td>Test Playlist for troubleshooting</td><td>%s/test.m3u8</td></tr>" % urljoin(SERVER_HOST,
																										SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write("<tr><td>Note 1:</td><td>Requires FFMPEG installation and setup</td></tr>")
		html.write("<tr><td>Note 2:</td><td>Requires External IP and port in advancedsettings</td></tr>")
		html.write("<tr><td>Note 3:</td><td>Requires TVH proxy setup in advancedsettings</td></tr></table>")
		html.write("</div></section></body></html>\n")


def close_menu(restart):
	with open("./cache/close.html", "w") as html:
		html.write("""<html><head><meta charset="UTF-8">%s</head><body>\n""" % (style,))
		html.write("<h1>Data Saved</h1>")
		if restart:
			html.write("<h1>You have change either the IP or Port, please restart this program.</h1>")
		else:
			html.write("<p>m3u8 url is %s/playlist.m3u8</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>kodi m3u8 url is %s/kodi.m3u8</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>EPG url is %s/epg.xml</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>Sports EPG url is %s/sports.xml</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>Plex Live TV url is %s</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>TVHeadend network url is %s/tvh.m3u8</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>External m3u8 url is %s/external.m3u8</p>" % urljoin(EXT_HOST, SERVER_PATH))
			html.write("<p>Combined m3u8 url is %s/combined.m3u8</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>Combined epg url is %s/combined.xml</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			html.write("<p>Static m3u8 url is %s/static.m3u8</p>" % urljoin(SERVER_HOST, SERVER_PATH))
			if TVHREDIRECT == True:
				html.write("<p>TVH's own EPG url is http://%s:9981/xmltv/channels</p>" % TVHURL)
		html.write("</body></html>\n")

def login_form():
	with open("./cache/login.html", "w") as html:
		html.write("""<html>
		<head>
		<meta charset="UTF-8">
		%s
		<title>YAP</title>
		</head>
		<body>\n""" % (style,))
		html.write('<section class="container"><div class="left-half">')
		html.write("<h1>YAP Settings</h1>")
		html.write('<form action="%s/%s/login" method="post">' % (SERVER_HOST, SERVER_PATH))

		html.write('<table width="300" border="2">')
		html.write('<tr><td>Username:</td><td><input name="user" value=""></td></tr>')
		html.write('<tr><td>Password:</td><td><input name="pass" type="Password" value=""></td></tr>')

		html.write('</table>')
		html.write('<input type="submit"  value="Submit">')
		html.write('</form>')

def restart_program():
	os.system('cls' if os.name == 'nt' else 'clear')
	args = sys.argv[:]
	logger.info('Re-spawning %s' % ' '.join(args))
	os.execl(sys.executable, *([sys.executable] + sys.argv))


############################################################
# authentication
############################################################


@login.user_loader
def user_loader(user_id):

	return User.query.get(user_id)

@app.route("/%s/login" % SERVER_PATH, methods=["GET","POST"])
def login():
	logger.debug("Login function")
	outcome = False
	user = ''
	baseurl = urljoin(SERVER_HOST, SERVER_PATH)

	# Local logon detection, free logon
	if request.environ.get('REMOTE_ADDR') and (request.environ.get('REMOTE_ADDR').startswith('10.') or request.environ.get('REMOTE_ADDR').startswith(
			'192.') or request.environ.get('REMOTE_ADDR').startswith('127.') or request.environ.get('REMOTE_ADDR').startswith('169.')):
		logger.debug("local logon")
		user = User.query.get('admin')
		outcome = True

	# checks for previous logon, free logon
	elif request.environ.get('REMOTE_ADDR'):
		user = User.query.get(str(request.environ.get('REMOTE_ADDR')))

		if user:
			outcome = True

	# checks for form return data
	elif request.form:
		logger.debug("Request form received.")
		inc_data = request.form
		uname = inc_data['user']
		pword = inc_data['pass']
		user = User.query.get(uname)
		if user:
			if user.username == uname and check_password_hash(user.password, pword):
				try:
					address = request.environ.get('REMOTE_ADDR')
					newuser = User(
						username=uname,
						address=address,
						password=generate_password_hash(pword))
					db.session.add(newuser)
					outcome = True
					logger.debug("Correct Password.")
				except:
					logger.error("No IP found.")


			else:
				logger.error("Wrong Password.")
		else:
			logger.error("User does not exist")
			return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'close.html')

	# Checks for url logon, ie kodi style
	elif request.args.get('user') and request.args.get('pass'):
		uname = request.args.get('user')
		pword = request.args.get('pass')
		user = User.query.get(uname)
		if user:
			if user.username == uname and check_password_hash(user.password, pword):
				try:
					address = request.environ.get('REMOTE_ADDR')
					newuser = User(
						username=uname,
						address=address,
						password=generate_password_hash(pword))
					db.session.add(newuser)
					outcome = True
					logger.debug("Correct Password.")
				except:
					logger.error("No IP found.")


			else:
				logger.error("Wrong Password.")
		else:
			logger.error("User does not exist")
			return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'close.html')

	if user and outcome:
		user.authenticated = True
		db.session.add(user)
		db.session.commit()
		login_user(user, remember=True)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = '%s/index.html' % baseurl
		return redirect(next_page)

	else:
		login_form()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'login.html')




@app.route("/logout", methods=["GET"])
@login_required
def logout():
	"""Logout the current user."""
	user = current_user
	user.authenticated = False
	db.session.add(user)
	db.session.commit()
	logout_user()
	logger.debug("Logged out")
	return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'close.html')


############################################################
# CLIENT <-> SSTV BRIDGE
############################################################
@app.route('/sstv/handle_data', methods=['POST'])
@login_required
def handle_data():
	logger.info("Received new settings from %s", request.environ.get('REMOTE_ADDR'))
	global playlist, kodiplaylist, QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, EXTIP, EXT_HOST, SERVER_HOST, EXTPORT
	inc_data = request.form
	config = {}
	if 'restart' in inc_data:
		if inc_data["restart"] == '3':
			logger.info('Updating YAP Dev')
			newfilename = ntpath.basename(latestfile)
			devname = latestfile.replace('master', 'dev')
			requests.urlretrieve(devname, os.path.join(os.path.dirname(sys.argv[0]), newfilename))
		elif inc_data["restart"] == '2':
			logger.info('Updating YAP')
			newfilename = ntpath.basename(latestfile)
			requests.urlretrieve(latestfile, os.path.join(os.path.dirname(sys.argv[0]), newfilename))
		logger.info('Restarting YAP')
		restart_program()
		return
	config["username"] = inc_data['Username']
	config["password"] = inc_data['Password']
	config["stream"] = inc_data['Stream']
	for sub in serverList:
		if sub[0] == inc_data['Server']:
			config["server"] = sub[1]
	for sub in providerList:
		if sub[0] == inc_data['Service']:
			config["service"] = sub[1]
	for sub in qualityList:
		if sub[0] == inc_data['Quality']:
			config["quality"] = sub[1]
	config["ip"] = inc_data['IP']
	config["port"] = int(inc_data['Port'])
	config["kodiport"] = int(inc_data['Kodiport'])
	config["externalip"] = inc_data['ExternalIP']
	config["externalport"] = inc_data['ExternalPort']
	QUAL = config["quality"]
	USER = config["username"]
	PASS = config["password"]
	SRVR = config["server"]
	SITE = config["service"]
	STRM = config["stream"]
	KODIPORT = config["kodiport"]
	if LISTEN_IP != config["ip"] or LISTEN_PORT != config["port"]:
		restartrequired = True
	else:
		restartrequired = False
	LISTEN_IP = config["ip"]
	LISTEN_PORT = config["port"]
	EXTIP = config["externalip"]
	EXTPORT = config["externalport"]
	EXT_HOST = "http://" + EXTIP + ":" + str(EXTPORT)
	SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
	with open('./proxysettings.json', 'w') as fp:
		dump(config, fp)
	logger.info("Updated Settings file.")
	check_token()
	playlist = build_playlist(SERVER_HOST)
	kodiplaylist = build_kodi_playlist()
	if restartrequired:
		logger.info("You have change either the IP or Port, please restart this program.")
		close_menu(True)
	else:
		close_menu(False)

	return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'close.html')


@app.route('/')
@app.route('/sstv')
@login_required
def landing_page():
	logger.info("Index was requested by %s", request.environ.get('REMOTE_ADDR'))
	create_menu()
	return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'settings.html')


@app.route('/<request_file>')
def index(request_file):
	logger.info("%s requested by %s at root" % (request_file, request.environ.get('REMOTE_ADDR')))
	if request_file.lower() == 'lineup_status.json':
		return status()
	elif request_file.lower() == 'discover.json':
		return discover()
	elif request_file.lower() == 'lineup.json':
		return lineup(chan_map)
	elif request_file.lower() == 'lineup.post':
		return lineup_post()
	# logger.debug(request.headers)
	elif request_file.lower() == 'device.xml':
		return device()
	elif request_file.lower() == 'favicon.ico':
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')


@app.route('/%s/<request_file>' % SERVER_PATH, methods=['GET','POST'])
def bridge(request_file):
	logger.info("%s requested by %s at root" % (request_file, request.environ.get('REMOTE_ADDR')))
	global playlist, token, chan_map, kodiplaylist, tvhplaylist, fallback
	check_token()
	try:
		client = find_client(request.headers['User-Agent'])
	except:
		logger.debug("No user-agent provided by %s", request.environ.get('REMOTE_ADDR'))
		client = 'unk'

	# External protection
	if not (request.environ.get('REMOTE_ADDR').startswith('10.') or request.environ.get('REMOTE_ADDR').startswith(
			'192.') or request.environ.get('REMOTE_ADDR').startswith('127.')):
		logger.info("REQUEST IS FROM AN EXTERNAL SOURCE")
		external = True
		if not request.args.get('password') or request.args.get('password') != EXTPASS:
			external_auth = False
		else:
			external_auth = True
	else:
		external = False
		external_auth = False

	# return epg
	if request_file.lower().startswith('epg.'):
		logger.info("EPG was requested by %s", request.environ.get('REMOTE_ADDR'))
		if not fallback:
			dl_epg()
		else:
			logger.exception("EPG build, EPG download failed. Trying SSTV.")
			dl_epg(2)
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml'), 'r+') as f:
			content = f.read()
		response = Response(content, mimetype='text/xml')
		headers = dict(response.headers)
		headers.update(
			{"Access-Control-Expose-Headers": "Accept-Ranges, Content-Encoding, Content-Length, Content-Range",
			 "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Range",
			 "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD"})
		response.headers = headers
		return response

	# return sports only epg
	if request_file.lower() == 'sports.xml':
		logger.info("Sports EPG was requested by %s", request.environ.get('REMOTE_ADDR'))
		if not fallback:
			dl_epg()
		else:
			logger.exception("Sports EPG build, EPG download failed. Trying SSTV.")
			dl_epg(2)
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'sports.xml')

	# return combined epg
	if request_file.lower() == 'combined.xml':
		logger.info("Combined EPG was requested by %s", request.environ.get('REMOTE_ADDR'))
		if not fallback:
			dl_epg()
		else:
			logger.exception("Combined EPG build, EPG download failed. Trying SSTV.")
			dl_epg(2)
		xmltv_merger()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'combined.xml')

	# return icons
	elif request_file.lower().endswith('.png'):
		logger.debug("Icon %s was requested by %s" % (request_file, request.environ.get('REMOTE_ADDR')))
		try:
			return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), request_file)
		except:
			return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')

	elif request_file.lower() == 'favicon.ico':
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')

	# return html epg guide based off of plex live
	elif request_file.lower().startswith('guide'):
		epgguide()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'guide.html')

	# return settings menu
	elif request_file.lower().startswith('index'):
		logger.info("Index was requested by %s", request.environ.get('REMOTE_ADDR'))
		create_menu()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'settings.html')

	# kodi static refresh
	elif request_file.lower().startswith('refresh'):
		# kodi force rescan 423-434
		logger.info("Refresh was requested by %s", request.environ.get('REMOTE_ADDR'))
		load_token()
		check_token()
		rescan_channels()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')

	# returns static playlist
	elif request_file.lower().startswith('static'):
		staticplaylist = build_static_playlist()
		logger.info("Static playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		return Response(staticplaylist, mimetype='application/x-mpegURL')

	# returns test playlist
	elif request_file.lower() == "test.m3u8":
		testplaylist = build_test_playlist([SERVER_HOST, EXT_HOST])
		logger.info("Static playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		return Response(testplaylist, mimetype='application/x-mpegURL')

	# returns kodi playlist
	elif request_file.lower().startswith('kodi'):
		kodiplaylist = build_kodi_playlist()
		logger.info("Kodi channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		return Response(kodiplaylist, mimetype='application/x-mpegURL')

	# returns combined playlist
	elif request_file.lower() == 'combined.m3u8':
		extraplaylist = build_playlist(SERVER_HOST) + obtain_m3u8()
		logger.info("Combined channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		logger.info("Sending playlist to %s", request.environ.get('REMOTE_ADDR'))
		return Response(extraplaylist, mimetype='application/x-mpegURL')

	# returns external playlist
	elif request_file.lower().startswith('external'):
		extplaylist = build_playlist(EXT_HOST)
		logger.info("External channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		return Response(extplaylist, mimetype='application/x-mpegURL')

	# returns tvh playlist
	elif request_file.lower().startswith('tvh'):
		tvhplaylist = build_tvh_playlist()
		logger.info("TVH channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		return Response(tvhplaylist, mimetype='application/x-mpegURL')

	elif request_file.lower() == 'playlist.m3u8' or request_file.lower().startswith('ch'):
		# returning Dynamic channels
		if request.args.get('ch') or request_file.lower().startswith('ch'):
			if request_file.lower().startswith('ch'):
				chan = request_file.lower().replace("ch", "").replace(".m3u8", "")
				sanitized_channel = "{:02.0f}".format(int(chan))
			else:
				chan = request.args.get('ch')
				sanitized_channel = ("0%d" % int(request.args.get('ch'))) if int(
					request.args.get('ch')) < 10 else request.args.get('ch')
			check_token()
			if SITE == 'vaders':
				logger.info("Channel %s playlist was requested by %s", sanitized_channel,
				            request.environ.get('REMOTE_ADDR'))
				vaders_url = "http://vaders.tv/live/{0}/{1}/{2}.{3}"
				strm = 'ts' if STRM == 'mpegts' else 'm3u8'
				channel_url = vaders_url.format('vsmystreams_' + USER, PASS, vaders_channels[chan], strm)
				return redirect(channel_url, code=302)

			qual = 1
			if request.args.get('qual') and int(sanitized_channel) <= 60:
				qual = request.args.get('qual')
			elif int(sanitized_channel) <= 60:
				qual = QUAL
			if request.args.get('strm') and request.args.get('strm') == 'rtmp':
				strm = 'rtmp'
				rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
				ss_url = rtmpTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])
			elif request.args.get('strm') and request.args.get('strm') == 'mpegts':
				strm = 'mpegts'
				return auto(sanitized_channel, qual)
			else:
				strm = 'hls'
				hlsTemplate = 'https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}=='
				hlsurl = hlsTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])
				ss_url = create_channel_playlist(sanitized_channel, qual, strm, token[
					'hash'])  # hlsTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])

			response = redirect(ss_url, code=302)
			headers = dict(response.headers)
			headers.update({'Content-Type': 'application/x-mpegURL', "Access-Control-Allow-Origin": "*"})
			response.headers = headers
			logger.info("Channel %s playlist was requested by %s", sanitized_channel,
						request.environ.get('REMOTE_ADDR'))
			# useful for debugging
			logger.debug("URL returned: %s" % ss_url)
			if request.args.get('type'):
				returntype = request.args.get('type')
			else:
				returntype = 3
			if strm == 'rtmp' or request.args.get('response'):
				logger.debug("returning response")
				return response
			elif returntype == 1 or client == 'kodi':
				hlsTemplate = 'https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}=='
				ss_url = hlsTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])
				# some players are having issues with http/https redirects
				logger.debug("returning hls url redirect")
				return redirect(ss_url, code=302)
			elif returntype == 2:
				logger.debug("returning m3u8 as file")
				return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'playlist.m3u8')
			elif returntype == 4 or client == 'vlc':
				logger.debug("returning hls url")
				return hlsurl
			else:
				# some players are having issues with http/https redirects
				logger.debug("returning m3u8 as variable")
				return ss_url

		# returning dynamic playlist
		else:
			playlist = build_playlist(SERVER_HOST)
			logger.info("All channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
			return Response(playlist, mimetype='application/x-mpegURL')

	# HDHomeRun emulated json files for Plex Live tv.
	elif request_file.lower() == 'lineup_status.json':
		return status()
	elif request_file.lower() == 'discover.json':
		return discover()
	elif request_file.lower() == 'lineup.json':
		if TVHREDIRECT == True:
			return tvh_lineup()
		else:
			return lineup(chan_map)
	elif request_file.lower() == 'lineup.post':
		return lineup_post()
	elif request_file.lower() == 'device.xml':
		return device()
	else:
		logger.info("Unknown requested %r by %s", request_file, request.environ.get('REMOTE_ADDR'))
		abort(404, "Unknown request")


@app.route('/tvh/<request_file>')
def tvh_returns(request_file):
	if request_file.lower() == 'lineup_status.json':
		return status()
	elif request_file.lower() == 'discover.json':
		return tvh_discover()
	elif request_file.lower() == 'lineup.json':
		return tvh_lineup()
	elif request_file.lower() == 'lineup.post':
		return lineup_post()
	elif request_file.lower() == 'device.xml':
		return tvh_device()
	else:
		logger.info("Unknown requested %r by %s", request_file, request.environ.get('REMOTE_ADDR'))
		abort(404, "Unknown request")


@app.route('/%s/auto/<request_file>' % SERVER_PATH)
@login_required
# returns a piped stream, used for TVH/Plex Live TV
def auto(request_file, qual=""):
	logger.debug("starting pipe function")
	check_token()
	channel = request_file.replace("v", "")
	logger.info("Channel %s playlist was requested by %s", channel,
				request.environ.get('REMOTE_ADDR'))
	sanitized_channel = ("0%d" % int(channel)) if int(channel) < 10 else channel

	sanitized_qual = '1'
	if int(channel) <= 60:
		if qual == "":
			sanitized_qual = QUAL
		else:
			sanitized_qual = qual
	template = "https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}"
	url = template.format(SRVR, SITE, sanitized_channel, sanitized_qual, token['hash'])
	logger.debug(
		"sanitized_channel: %s sanitized_qual: %s QUAL: %s qual: %s" % (sanitized_channel, sanitized_qual, QUAL, qual))
	logger.debug(url)
	# try:
	# 	urllib.request.urlopen(url, timeout=2).getcode()
	# except:
	# 	a = 1
	# except timeout:
	# 	#special arg for tricking tvh into saving every channel first time
	# 	print("timeout")
	# 	sanitized_channel = '01'
	# 	sanitized_qual = '3'
	# 	url = template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	if 'tvh' in sys.argv:
		logger.debug("TVH Trickery happening")
		sanitized_channel = '01'
		sanitized_qual = '3'
		url = template.format(SRVR, SITE, sanitized_channel, sanitized_qual, token['hash'])
		logger.debug(url)
	if request.args.get('url'):
		logger.info("Piping custom URL")
		url = request.args.get('url')
		if '|' in url:
			url = url.split('|')[0]
		logger.debug(url)
	import subprocess

	def generate():
		logger.debug("starting generate function")
		cmdline = list()
		cmdline.append(FFMPEGLOC)
		cmdline.append("-i")
		cmdline.append(url)
		cmdline.append("-vcodec")
		cmdline.append("copy")
		cmdline.append("-acodec")
		cmdline.append("copy")
		cmdline.append("-f")
		cmdline.append("mpegts")
		cmdline.append("pipe:1")
		logger.debug(cmdline)
		FNULL = open(os.devnull, 'w')
		proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=FNULL)
		logger.debug("pipe started")
		try:
			f = proc.stdout
			byte = f.read(512)
			while byte:
				yield byte
				byte = f.read(512)

		finally:
			proc.kill()

	return Response(response=generate(), status=200, mimetype='video/mp2t',
					headers={'Access-Control-Allow-Origin': '*', "Content-Type": "video/mp2t",
							 "Content-Disposition": "inline", "Content-Transfer-Enconding": "binary"})


############################################################
# MAIN
############################################################


if __name__ == "__main__":
	logger.info("Initializing")
	load_settings()
	try:
		User.query.all()
	except:
		print("Error parsing ext user list")
	if os.path.exists(TOKEN_PATH):
		load_token()
	check_token()
	fallback = False

	logger.info("Building initial playlist...")
	try:
		# fetch chan_map
		try:
			chan_map = build_channel_map()
		except:
			# cannot get response from fog, resorting to fallback
			fallback = True
			chan_map = build_channel_map_sstv()
		playlist = build_playlist(SERVER_HOST)
		kodiplaylist = build_kodi_playlist()
		tvhplaylist = build_tvh_playlist()
		# Download icons, runs in sep thread, takes ~1min
		try:
			di = threading.Thread(target=dl_icons, args=(len(chan_map),))
			di.setDaemon(True)
			di.start()
		except (KeyboardInterrupt, SystemExit):
			sys.exit()
	except:
		logger.exception("Exception while building initial playlist: ")
		exit(1)

	try:
		thread.start_new_thread(thread_playlist, ())
	except:
		_thread.start_new_thread(thread_playlist, ())

	print("\n\n##############################################################")
	print("Main Menu - %s/index.html" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Contains all the information located here and more!")
	print("##############################################################\n\n")
	print("\n##############################################################")
	print("m3u8 url is %s/playlist.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("kodi m3u8 url is %s/kodi.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("EPG url is %s/epg.xml" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Sports EPG url is %s/sports.xml" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Plex Live TV url is %s" % urljoin(SERVER_HOST, SERVER_PATH))
	print("TVHeadend network url is %s/tvh.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("External m3u8 url is %s/external.m3u8" % urljoin(EXT_HOST, SERVER_PATH))
	print("Combined m3u8 url is %s/combined.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Combined EPG url is %s/combined.xml" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Static m3u8 url is %s/static.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("TVH's own EPG url is http://%s:9981/xmltv/channels" % TVHURL)
	print("##############################################################\n")

	if __version__ < latest_ver:
		logger.info(
			"Your version (%s%s) is out of date, the latest is %s, which has now be downloaded for you into the 'updates' subdirectory." % (
			type, __version__, latest_ver))
		newfilename = ntpath.basename(latestfile)
		if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), 'updates')):
			os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), 'updates'))
		requests.urlretrieve(latestfile, os.path.join(os.path.dirname(sys.argv[0]), 'updates', newfilename))
	else:
		logger.info("Your version (%s) is up to date." % (__version__))
	logger.info("Listening on %s:%d at %s/", LISTEN_IP, LISTEN_PORT, urljoin(SERVER_HOST, SERVER_PATH))
	try:
		a = threading.Thread(target=thread_updater)
		a.setDaemon(True)
		a.start()
	except (KeyboardInterrupt, SystemExit):
		sys.exit()
	if netdiscover:
		try:
			a = threading.Thread(target=udpServer)
			a.setDaemon(True)
			a.start()
		except (KeyboardInterrupt, SystemExit):
			sys.exit()
	# debug causes it to load twice on initial startup and every time the script is saved, TODO disbale later
	try:
		app.run(host=LISTEN_IP, port=LISTEN_PORT, threaded=True, debug=False)
	except:
		os.system('cls' if os.name == 'nt' else 'clear')
		logger.exception("Proxy failed to launch, try another port")
	logger.info("Finished!")
