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
import datetime as dt
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
from xml.sax.saxutils import escape
HEADLESS = False
try:
	import tkinter
except:
	HEADLESS = True
	
if 'headless' in sys.argv:
	HEADLESS = True

try:
	from urlparse import urljoin
	import thread
except ImportError:
	from urllib.parse import urljoin
	import _thread

from flask import Flask, redirect, abort, request, Response, send_from_directory, jsonify, render_template, \
	stream_with_context, url_for

app = Flask(__name__, static_url_path='')

__version__ = 1.7
# Changelog
# 1.7 - Static and dynamic xspf options added  ip:port/sstv/static.xspf or ip:port/sstv/playlist.xspf
# 1.691 - Updated FOG Urls
# 1.69 - Added more info to website, removed network discovery(isn't useful).
# 1.68 - Updated for MyStreams changes
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

class programinfo:
	description = ""
	channel = 0
	channelname = ""
	height = 0
	startTime = 0
	endTime = 0
	timeRange = ""
	_title = ""
	_category = ""
	_quality = ""
	_language = ""


	def get_title(self):
		if len(self._title) == 0:
			return ("none " + self.timeRange).strip()
		else:
			return (self._title + " " + self.quality + " " + self.timeRange).replace("  ", " ").strip()


	def set_title(self, title):
		self._title = title
		if len(self._category) == 0 or self._category == "TVShows":
			if title.startswith("NHL") or title.lower().find("hockey"):
				self._category = "Ice Hockey"
			elif title.startswith("UEFA") or title.startswith("EPL") or title.startswith(
					"Premier League") or title.startswith("La Liga") or title.startswith("Bundesliga") or title.startswith(
					"Serie A") or title.lower().find("soccer"):
				self._category = "World Football"
			elif title.startswith("MLB") or title.lower().find("baseball"):
				self._category = "Baseball"
			elif title.startswith("MMA") or title.startswith("UFC") or title.lower().find("boxing"):
				self._category = "Boxing + MMA"
			elif title.startswith("NCAAF") or title.startswith("CFB"):
				self._category = "NCAAF"
			elif title.startswith("ATP") or title.lower().find("tennis"):
				self._category = "Tennis"
			elif title.startswith("WWE"):
				self._category = "Wrestling"
			elif title.startswith("NFL") or title.startswith("NBA"):
				self._category = title.split(" ")[0].replace(":", "").strip()


	title = property(get_title, set_title)


	def get_category(self):
		if (len(self._category) == 0 or self._category == "none") and (
			self.title.lower().find("news") or self.description.lower().find("news")) > -1:
			return "News"
		else:
			return self._category


	def set_category(self, category):
		if category == "tv":
			self._category = ""
		else:
			self._category = category


	category = property(get_category, set_category)


	def get_language(self):
		return self._language


	def set_language(self, language):
		if language.upper() == "US" or language.upper() == "EN":
			self._language = ""
		else:
			self._language = language.upper()


	language = property(get_language, set_language)


	def get_quality(self):
		return self._quality


	def set_quality(self, quality):
		if quality.endswith("x1080"):
			self._quality = "1080i"
			self.height = 1080
		elif quality.endswith("x720") or quality.lower() == "720p":
			self._quality = "720p"
			self.height = 720
		elif quality.endswith("x540") or quality.lower() == "hqlq":
			self._quality = "540p"
			self.height = 540
		elif quality.find("x") > 2:
			self._quality = quality
			self.height = int(quality.split("x")[1])
		else:
			self._quality = quality
			self.height = 0


	quality = property(get_quality, set_quality)


	def get_album(self):
		if self._quality.upper() == "HQLQ" and self.channelname.upper().find(" 720P") > -1:
			self._quality = "720p"
		return (self._category + " " + self.quality + " " + self._language).strip().replace("  ", " ")


	album = property(get_album)


class EST5EDT(dt.tzinfo):

	def utcoffset(self, dt):
		return timedelta(hours=-5) + self.dst(dt)

	def utc_seconds(self):
		return self.utcoffset(datetime.now()).total_seconds()

	def dst(self, dt):
		d = datetime(dt.year, 3, 8)  # 2nd Sunday in March
		self.dston = d + timedelta(days=6 - d.weekday())
		d = datetime(dt.year, 11, 1)  # 1st Sunday in Nov
		self.dstoff = d + timedelta(days=6 - d.weekday())
		if self.dston <= dt.replace(tzinfo=None) < self.dstoff:
			return timedelta(hours=1)
		else:
			return timedelta(0)

	def tzname(self, dt):
		return 'EST5EDT'
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
EXTM3URL = ''
EXTM3UNAME = ''
EXTM3UFILE = ''
EXTXMLURL = ''
TVHREDIRECT = False
TVHURL = '127.0.0.1'
TVHUSER = ''
TVHPASS = ''
tvhWeight = 300  # subscription priority
tvhstreamProfile = 'pass'  # specifiy a stream profile that you want to use for adhoc transcoding in tvh, e.g. mp4
GUIDELOOKAHEAD = 5 #minutes

# LINUX/WINDOWS
if platform.system() == 'Linux':
	FFMPEGLOC = '/usr/bin/ffmpeg'
	if os.path.isdir(os.path.join(os.path.expanduser("~"), '.kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), '.kodi', 'userdata', 'addon_data', 'pvr.iptvsimple')
	else:
		ADDONPATH = False
elif platform.system() == 'Windows':
	FFMPEGLOC = os.path.join('C:\FFMPEG', 'bin', 'ffmpeg.exe')
	if os.path.isdir(os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Kodi', 'userdata', 'addon_data',
								  'pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Kodi', 'userdata', 'addon_data',
								 'pvr.iptvsimple')
	else:
		ADDONPATH = False
elif platform.system() == 'Darwin':
	FFMPEGLOC = '/usr/local/bin/ffmpeg'
	if os.path.isdir(
			os.path.join(os.path.expanduser("~"), "Library", "Application Support", 'Kodi', 'userdata', 'addon_data',
						 'pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), "Library", "Application Support", 'Kodi', 'userdata',
								 'addon_data', 'pvr.iptvsimple')
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
			if "tvhredirect" in advconfig:
				logger.debug("Overriding tvhredirect")
				global TVHREDIRECT
				TVHREDIRECT = advconfig["tvhredirect"]
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


def load_settings():
	global QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, SERVER_HOST, EXTIP, EXT_HOST, EXTPORT
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
				if SITE == "mmatv":
					SITE = "viewmmasr"
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
		if HEADLESS:
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
			config["port"] = int(input("and port?(ie 99, do not use 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			config["kodiport"] = int(input("Kodiport? (def is 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			config["externalip"] = input("External IP?")
			config["externalport"] = int(input("and ext port?(ie 99, do not use 8080)"))
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
		else:
			root = tkinter.Tk()
			root.title("YAP Setup")
			# root.geometry('750x600')
			app = GUI(root)  # calling the class to run
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

if not HEADLESS:
	class ToggledFrame(tkinter.Frame):
		def __init__(self, parent, text="", *args, **options):
			tkinter.Frame.__init__(self, parent, *args, **options)

			self.show = tkinter.IntVar()
			self.show.set(0)
			self.title_frame = tkinter.Frame(self)
			self.title_frame.pack(fill="x", expand=1)

			tkinter.Label(self.title_frame, text=text).pack(side="left", fill="x", expand=1)

			self.toggle_button = tkinter.Checkbutton(self.title_frame, width=2, text='+', command=self.toggle,
			                                         variable=self.show)
			self.toggle_button.pack(side="left")

			self.sub_frame = tkinter.Frame(self, relief="sunken", borderwidth=1)

		def toggle(self):
			if bool(self.show.get()):
				self.sub_frame.pack(fill="x", expand=1)
				self.toggle_button.configure(text='-')
			else:
				self.sub_frame.forget()
				self.toggle_button.configure(text='+')

	class GUI(tkinter.Frame):
		def client_exit(self, root):
			root.destroy()


		def __init__(self, master):
			tkinter.Frame.__init__(self, master)
			self.t1 = tkinter.StringVar()
			self.t1.set("Minimum Settings")
			t1 = tkinter.Label(master, textvariable=self.t1, height=2)
			t1.grid(row=1, column=2)

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

			self.labelSite = tkinter.StringVar()
			self.labelSite.set("Site")
			labelSite = tkinter.Label(master, textvariable=self.labelSite, height=2)
			labelSite.grid(row=4, column=1)

			userSite = tkinter.StringVar()
			userSite.set('StreamTVnow')
			self.site = tkinter.OptionMenu(master, userSite, *[x[0] for x in providerList])
			self.site.grid(row=4, column=2)

			t2 = ToggledFrame(master, text='Optional', relief="raised", borderwidth=1)
			t2.grid(row=5, column=1, columnspan=3)

			self.labelServer = tkinter.StringVar()
			self.labelServer.set("Server")
			labelServer = tkinter.Label(t2.sub_frame, textvariable=self.labelServer, height=2)
			labelServer.grid(row=1, column=1)

			userServer = tkinter.StringVar()
			userServer.set('East-NY')
			self.server = tkinter.OptionMenu(t2.sub_frame, userServer, *[x[0] for x in serverList])
			self.server.grid(row=1, column=2)

			self.labelStream = tkinter.StringVar()
			self.labelStream.set("Stream Type")
			labelStream = tkinter.Label(t2.sub_frame, textvariable=self.labelStream, height=2)
			labelStream.grid(row=2, column=1)

			userStream = tkinter.StringVar()
			userStream.set('HLS')
			self.stream = tkinter.OptionMenu(t2.sub_frame, userStream, *[x.upper() for x in streamtype])
			self.stream.grid(row=2, column=2)

			self.labelQuality = tkinter.StringVar()
			self.labelQuality.set("Quality")
			labelQuality = tkinter.Label(t2.sub_frame, textvariable=self.labelQuality, height=2)
			labelQuality.grid(row=3, column=1)

			userQuality = tkinter.StringVar()
			userQuality.set('HD')
			self.quality = tkinter.OptionMenu(t2.sub_frame, userQuality, *[x[0] for x in qualityList])
			self.quality.grid(row=3, column=2)

			self.labelIP = tkinter.StringVar()
			self.labelIP.set("Listen IP")
			labelIP = tkinter.Label(t2.sub_frame, textvariable=self.labelIP, height=2)
			labelIP.grid(row=4, column=1)

			userIP = tkinter.StringVar()
			userIP.set(LISTEN_IP)
			self.ip = tkinter.Entry(t2.sub_frame, textvariable=userIP, width=30)
			self.ip.grid(row=4, column=2)

			self.noteIP = tkinter.StringVar()
			self.noteIP.set("If using on other machines then set a static IP and use that.")
			noteIP = tkinter.Label(t2.sub_frame, textvariable=self.noteIP, height=2)
			noteIP.grid(row=4, column=3)

			self.labelPort = tkinter.StringVar()
			self.labelPort.set("Listen Port")
			labelPort = tkinter.Label(t2.sub_frame, textvariable=self.labelPort, height=2)
			labelPort.grid(row=5, column=1)

			userPort = tkinter.IntVar()
			userPort.set(LISTEN_PORT)
			self.port = tkinter.Entry(t2.sub_frame, textvariable=userPort, width=30)
			self.port.grid(row=5, column=2)

			self.notePort = tkinter.StringVar()
			self.notePort.set("If 80 doesn't work try 99")
			notePort = tkinter.Label(t2.sub_frame, textvariable=self.notePort, height=2)
			notePort.grid(row=5, column=3)

			t3 = ToggledFrame(master, text='Advanced', relief="raised", borderwidth=1)
			t3.grid(row=6, column=1, columnspan=3)

			self.labelKodiPort = tkinter.StringVar()
			self.labelKodiPort.set("KodiPort")
			labelKodiPort = tkinter.Label(t3.sub_frame, textvariable=self.labelKodiPort, height=2)
			labelKodiPort.grid(row=1, column=1)

			userKodiPort = tkinter.IntVar(None)
			userKodiPort.set(KODIPORT)
			self.kodiport = tkinter.Entry(t3.sub_frame, textvariable=userKodiPort, width=30)
			self.kodiport.grid(row=1, column=2)

			self.noteKodiPort = tkinter.StringVar()
			self.noteKodiPort.set("Only change if you've had to change the Kodi port")
			noteKodiPort = tkinter.Label(t3.sub_frame, textvariable=self.noteKodiPort, height=2)
			noteKodiPort.grid(row=1, column=3)

			self.labelExternalIP = tkinter.StringVar()
			self.labelExternalIP.set("External IP")
			labelExternalIP = tkinter.Label(t3.sub_frame, textvariable=self.labelExternalIP, height=2)
			labelExternalIP.grid(row=2, column=1)

			userExternalIP = tkinter.StringVar()
			userExternalIP.set(EXTIP)
			self.externalip = tkinter.Entry(t3.sub_frame, textvariable=userExternalIP, width=30)
			self.externalip.grid(row=2, column=2)

			self.noteExternalIP = tkinter.StringVar()
			self.noteExternalIP.set("Enter your public IP or Dynamic DNS,\nfor use when you wish to use this remotely.")
			noteExternalIP = tkinter.Label(t3.sub_frame, textvariable=self.noteExternalIP, height=2)
			noteExternalIP.grid(row=2, column=3)

			self.labelExternalPort = tkinter.StringVar()
			self.labelExternalPort.set("External Port")
			labelExternalPort = tkinter.Label(t3.sub_frame, textvariable=self.labelExternalPort, height=2)
			labelExternalPort.grid(row=3, column=1)

			userExternalPort = tkinter.IntVar(None)
			userExternalPort.set(EXTPORT)
			self.extport = tkinter.Entry(t3.sub_frame, textvariable=userExternalPort, width=30)
			self.extport.grid(row=3, column=2)

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
				global playlist, kodiplaylist, QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, EXTIP, EXT_HOST, SERVER_HOST, EXTPORT
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


				self.labelSetting1 = tkinter.StringVar()
				self.labelSetting1.set("Open a web browser and go to %s for instructions and output URLs." % urljoin(SERVER_HOST, SERVER_PATH))
				labelSetting1 = tkinter.Label(master, textvariable=self.labelSetting1, height=2)
				labelSetting1.grid(row=1)

				self.labelFooter = tkinter.StringVar()
				self.labelFooter.set("URLs can also be found later on the YAP main screen after each launch")
				labelFooter = tkinter.Label(master, textvariable=self.labelFooter, height=4)
				labelFooter.grid(row=2)

				button1 = tkinter.Button(master, text="Launch YAP!!", width=20,
										 command=lambda: self.client_exit(master))
				button1.grid(row=3)

			button1 = tkinter.Button(master, text="Submit", width=20, command=lambda: gather())
			button1.grid(row=7, column=1, columnspan=3)



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
	if source == 1:
		logger.info("Downloading epg")
		requests.urlretrieve("https://fast-guide.smoothstreams.tv/altepg/xmltv5.xml.gz",
							 os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml.gz'))
		unzipped = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml.gz')
		to_process.append([unzipped, "epg.xml", 'fog'])
		requests.urlretrieve("https://fast-guide.smoothstreams.tv/feed.xml",
							 os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawsports.xml'))
		unzippedsports = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawsports.xml')
		to_process.append([unzippedsports, "sports.xml", 'sstv'])
	else:
		logger.info("Downloading sstv epg")
		requests.urlretrieve("https://fast-guide.smoothstreams.tv/feed.xml",
							 os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml'))
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
				newname = [chan_map[x].channum for x in range(len(chan_map) + 1) if
						   x != 0 and chan_map[x].epg == a.attrib['id'] and chan_map[x].channame == b.text]
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
				if process[2] == 'sstv':
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

def getProgram(channel):
	global jsonGuide1, jsonGuide2
	tmNow = time.localtime(time.time() + GUIDELOOKAHEAD * 60)
	sched_offest = EST5EDT().utc_seconds()
	retVal = programinfo()
	local_off = datetime.utcoffset(datetime.utcnow().replace(tzinfo=dt.timezone.utc).astimezone(tz=None)).total_seconds()
	if str(int(channel)) in jsonGuide1:
		oChannel = jsonGuide1[str(int(channel))]
		retVal.channel = channel
		retVal.channelname = oChannel["name"].replace(format(channel, "02") + " - ", "").strip()
		for item in oChannel["items"]:
			startTime = time.localtime(time.mktime(datetime.strptime(item["time"], '%Y-%m-%d %H:%M:%S').timetuple()) - sched_offest + local_off)
			endTime = time.localtime(time.mktime(datetime.strptime(item["end_time"], '%Y-%m-%d %H:%M:%S').timetuple()) - sched_offest + local_off)
			if startTime < tmNow and endTime > tmNow:
				retVal.category = item["category"].strip()
				retVal.quality = item["quality"].upper()
				retVal.language = item["language"].upper()
				retVal.title = item["name"].strip()
				retVal.description = item["description"].strip()
				retVal.channel = channel
				retVal.startTime = startTime
				retVal.endTime = endTime
				retVal.timeRange = time.strftime("%H:%M", startTime) + "-" + time.strftime("%H:%M", endTime)
				return retVal
	if str(int(channel)) in jsonGuide2:
		oChannel = jsonGuide2[str(int(channel))]
		retVal.channel = channel
		retVal.channelname = oChannel["name"].replace(format(channel, "02") + " - ", "").strip()
		for item in oChannel["items"]:
			startTime = time.strptime(item["time"], '%Y-%m-%d %H:%M:%S')
			endTime = time.strptime(item["end_time"], '%Y-%m-%d %H:%M:%S')
			if startTime < tmNow and endTime > tmNow:
				retVal.category = item["category"].strip()
				retVal.quality = item["quality"].upper()
				retVal.language = item["language"].upper()
				retVal.title = item["name"].strip()
				retVal.description = item["description"].strip()
				retVal.channel = channel
				retVal.startTime = startTime
				retVal.endTime = endTime
				retVal.timeRange = time.strftime("%H:%M", startTime) + "-" + time.strftime("%H:%M", endTime)
				return retVal

	return retVal


def getJSON(sFile, sURL, sURL2):
	try:
		if os.path.isfile(sFile) and time.time() - os.stat(sFile).st_mtime < 3600:
			retVal = json.loads(open(sFile, 'r').read())
			return retVal
	except:
		pass

	try:
		sJSON = urllib.request.urlopen(sURL).read().decode("utf-8")
		retVal = json.loads(sJSON)
	except:
		try:
			sJSON = urllib.request.urlopen(sURL2).read().decode("utf-8")
			retVal = json.loads(sJSON)
		except:
			return json.loads("{}")

	try:
		file = open(sFile, "w+")
		file.write(sJSON)
		file.close()
	except:
		pass

	return retVal

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
	url = 'https://fast-guide.smoothstreams.tv/altepg/channels.json'
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

def build_xspf(host, request_file):
	# standard dynamic playlist
	global chan_map

	xspfBodyTemplate = ('<?xml version="1.0" encoding="UTF-8"?>\n' +
		 '<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n' +
		'\t<title>Playlist</title>\n' +
		'\t<trackList>\n' +
		'{0}' +
		'\t</trackList>\n' +
		'\t<extension application="http://www.videolan.org/vlc/playlist/0">\n' +
		'{1}' +
		'\t</extension>\n' +
		'</playlist>')
	xspfTrackTemplate = ('\t\t<track>\n' +
		'\t\t\t<location>{5}</location>\n' +
		'\t\t\t<title>{3}</title>\n' +
		'\t\t\t<creator>{8}</creator>\n' +
		'\t\t\t<album>{0}</album>\n' +
		'\t\t\t<trackNum>{6}</trackNum>\n' +
		'\t\t\t<annotation>{9}</annotation>\n' +
		'\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n' +
		'\t\t\t\t<vlc:id>{7}</vlc:id>\n' +
		'\t\t\t</extension>\n' +
		'\t\t</track>\n')
	xspfTrack2Template = '\t\t<vlc:item tid="{0}"/>\n'
	xspfTracks = ""
	xspfTracks2 = ""


	# build playlist using the data we have
	for pos in range(1, len(chan_map) + 1):
		# build channel url

		program = getProgram(pos)
		url = "{0}/playlist.m3u8?ch={1}"
		vaders_url = "http://vaders.tv/live/{0}/{1}/{2}.{3}"
		quality = '720p' if QUAL == '1' or pos > 60 else '540p' if QUAL == '2' else '360p'
		if SITE == 'vaders':
			strm = 'ts' if STRM == 'mpegts' else 'm3u8'
			channel_url = vaders_url.format('vsmystreams_' + USER,PASS, vaders_channels[str(pos)], strm)
		else:
			urlformatted = url.format(SERVER_PATH, chan_map[pos].channum)
			template = '{0}://{1}.smoothstreams.tv:{2}/{3}/ch{4}q{5}.stream{6}?wmsAuthSign={7}'
			if not 'static' in request_file:
				channel_url = urljoin(host, urlformatted)
			else:
				channel_url = template.format('https' if STRM == 'hls' else 'rtmp', SRVR, '443' if STRM == 'hls' else '3625',
										   SITE, "{:02}".format(pos), QUAL if pos <= 60 else '1',
										   '/playlist.m3u8' if STRM == 'hls' else '', token['hash'])
		# build playlist entry
		try:
			xspfTracks += xspfTrackTemplate.format(escape(program.album), escape(program.quality),
												   escape(program.language), escape(program.title),
												   str(program.channel), channel_url,
												   str(int(chan_map[pos].channum)),
												   str(int(chan_map[pos].channum) -1 ),
												   escape(program.channelname), escape(program.description))
			xspfTracks2 += xspfTrack2Template.format(str(int(chan_map[pos].channum) - 1))


		except:
			logger.exception("Exception while updating playlist: ")
	xspf = xspfBodyTemplate.format(xspfTracks, xspfTracks2)
	logger.debug("Built xspf playlist")

	return xspf


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
				chan_map[pos].channum,
				name)
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
	body { background: white url("https://guide.smoothstreams.tv/assets/images/channels/150.png") no-repeat fixed center center; background-size: 500px 500px; color: black; }
	h1 { color: white; background-color: black; padding: 0.5ex }
	h2 { color: white; background-color: black; padding: 0.3ex }
	.container {display: table; width: 100%;}
	.left-half {position: absolute;  left: 0px;  width: 50%;}
	.right-half {position: absolute;  right: 0px;  width: 50%;}
</style>
"""


def create_menu():
	footer = '<p>Donations: PayPal to vorghahn.sstv@gmail.com  or BTC - 19qvdk7JYgFruie73jE4VvW7ZJBv8uGtFb</p>'
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
		template = "<a href='{1}/{2}/{0}.html'>{3}</a>"
		html.write("<p>" + template.format("settings",SERVER_HOST, SERVER_PATH,"Options") + " " + template.format("howto",SERVER_HOST, SERVER_PATH,"Instructions") + " " + template.format("channels",SERVER_HOST, SERVER_PATH,"Channels List") + "</p>")

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
		html.write(footer)
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
		html.write("<tr><td>Dynamic xspf, includes currently showing programs</td><td>%s/playlist.xspf</td></tr>" % urljoin(SERVER_HOST,
																										SERVER_PATH))
		html.write("<tr><td>Static xspf</td><td>%s/static.xspf</td></tr>" % urljoin(SERVER_HOST,
																										SERVER_PATH))
		html.write("<tr><td>&nbsp;</td><td>&nbsp;</td></tr>")
		html.write("<tr><td>Note 1:</td><td>Requires FFMPEG installation and setup</td></tr>")
		html.write("<tr><td>Note 2:</td><td>Requires External IP and port in advancedsettings</td></tr>")
		html.write("<tr><td>Note 3:</td><td>Requires TVH proxy setup in advancedsettings</td></tr></table>")
		html.write("</div></section></body></html>\n")


	with open("./cache/channels.html", "w") as html:
		global chan_map
		html.write("""<html><head><title>YAP</title><meta charset="UTF-8">%s</head><body>\n""" % (style,))
		html.write("<h1>Channel List and Upcoming Shows</h1>")
		template = "<a href='{1}/{2}/{0}.html'>{3}</a>"
		html.write("<p>" + template.format("settings",SERVER_HOST, SERVER_PATH,"Options") + " " + template.format("howto",SERVER_HOST, SERVER_PATH,"Instructions") + " " + template.format("channels",SERVER_HOST, SERVER_PATH,"Channels List") + "</p>")
		html.write('<section class="container"><div class="left-half"><table width="300" border="1">')
		template = "<td>{0}</td><td><a href='{2}/{3}/playlist.m3u8?ch={0}'><img src='{2}/{3}/{0}.png'></a></td></td>"
		for i in chan_map:
			if i%5 == 1:
				html.write("<tr>")
			html.write(template.format(chan_map[i].channum, chan_map[i].channame, SERVER_HOST, SERVER_PATH))
			if i%5 == 0:
				html.write("</tr>")
		html.write("</table>")
		html.write("</br>%s</div>" % footer)
		html.write('<div class="right-half"><h3>Coming up</h3>')
		template = "{0} - <a href='{2}/{3}/playlist.m3u8?ch={0}'>{1}</a></br>"
		for i in chan_map:
			prog = getProgram(i)
			if prog.title != 'none':
				html.write(template.format(chan_map[i].channum, prog.title, SERVER_HOST, SERVER_PATH))
		html.write("</div></section>")
		html.write("</body></html>\n")

	with open("./cache/index.html", "w") as html:
		html.write("""<html><head><title>YAP</title><meta charset="UTF-8">%s</head><body>\n""" % (style,))
		template = "<h2><a href='{1}/{2}/{0}.html'>{3}</a></h2>"
		html.write("<h1>Welcome to YAP!</h1>")
		html.write(template.format("settings",SERVER_HOST, SERVER_PATH,"Options"))
		html.write(template.format("howto",SERVER_HOST, SERVER_PATH,"Instructions"))
		html.write(template.format("channels",SERVER_HOST, SERVER_PATH,"Channels List"))
		html.write(footer)
		html.write("</body></html>\n")

	with open("./cache/howto.html", "w") as html:
		html.write("""<html><head><title>YAP</title><meta charset="UTF-8">%s</head><body>\n""" % (style,))
		template = "<a href='{1}/{2}/{0}.html'>{3}</a>"
		html.write("<h1>Welcome to YAP!</h1>")
		html.write("<p>" + template.format("settings",SERVER_HOST, SERVER_PATH,"Options") + " " + template.format("howto",SERVER_HOST, SERVER_PATH,"Instructions") + " " + template.format("channels",SERVER_HOST, SERVER_PATH,"Channels List") + "</p>")
		html.write("<h2>Work in progress.</h2>")

		html.write("""<h2>Commandline Arguments</h2></br><p>'install' - forces recreation of the install function which creates certain files, such as the tvh internal grabber</br></br>
'headless' - uses command line for initial setup rather than gui</br></br>
'tvh' - each call to a piped channel will return channel 01 which is a 24/7 channel so will always generate a positive result, this allows TVH to create all services</p></br>""")

		html.write("<h2><a href='https://seo-michael.co.uk/how-to-setup-livetv-pvr-simple-xbmc-kodi/'>Kodi Setup</a></h2>")
		html.write("<p>Use this information to populate the settings:</p>")
		html.write("<p>m3u8 - %s/kodi.m3u8</p>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write("<p>EPG - %s/epg.xml</p>" % urljoin(SERVER_HOST, SERVER_PATH))
		html.write('''<p>RTMP is an issue so there's a special playlist for it (kodi.m3u8), it has two of every channel in both rtmp and hls, in kodi Tv use the Left hand menu  and select group or filter. Then select dynamic (forced hls) or static rtmp.For static_refresh channel (151) don't use it on the guide page, use it on the channel list page. Otherwise kodi will crash. This will lock kodi for about 20secs but refresh the playlist.</p>''')

		html.write("<h2>Ensure you can get YAP working in Kodi or VLC first before attmepting Plex or TVHeadend!</h2>")
		html.write("<h2><a href='https://imgur.com/a/OZkN0'>Plex Setup</a></h2>")
		html.write("<p></p>")

		html.write("<h2>TVHeadend Setup</h2>")
		html.write("""<p>
In a nutshell here is how to do it on Ubuntu.</br>Replace USERNAME with your linux user:</br>

<b>1 Download the latest sstvProxy binary (exe) from:</b></br>
http://smoothstreams.tv/board/index.php?topic=1832.0</br>
Save it to:</br>
<blockquote><i>/home/USERNAME/Desktop/sstv</i></blockquote></br>
</br>
<b>2 Delete proxysettings.json</b> (only if you're coming from an older version of sstvproxy)</br>
<blockquote><i>sudo rm /home/USERNAME/Desktop/sstv/proxysettings.json</i></blockquote></br>
</br>
<b>3 Install ffmpeg:</b></br>
<blockquote><i>sudo apt install ffmpeg jq</i></blockquote></br>
</br>
<b>4 Install tvheadend:</b></br>
<blockquote><i>sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61 </i></blockquote></br>
<blockquote><i>echo "deb https://dl.bintray.com/tvheadend/deb xenial release-4.2" | sudo tee -a /etc/apt/sources.list</i></blockquote></br>
<blockquote><i>sudo apt-get update</i></blockquote></br>
<blockquote><i>sudo apt-get install tvheadend</i></blockquote></br>
You will need to enter a username and password to manage tvheadend as part of this install process.</br>
Check for the presence of /usr/bin/tv_find_grabbers If it doesnt exist then run:</br>
<blockquote><i>"apt-get install xmltv-util" </i></blockquote></br>
</br>
<b>5 Run sstvProxy:</b></br>
<blockquote><i>sudo chmod +x /home/USERNAME/Desktop/sstv/sstvProxy </i></blockquote></br>
<blockquote><i>sudo /home/USERNAME/Desktop/sstv/sstvProxy tvh</i></blockquote> <i>note the 'tvh' switch will enable it to scan all 150 channels</i></br>
Go through the setup steps, this will also setup the internal EPG grabber for TVHeadend</br>
</br>
<b>6 Restart TVHeadend:</b></br>
<blockquote><i>systemctl stop tvheadend </i></blockquote></br>
<blockquote><i>systemctl start tvheadend </i></blockquote></br>
</br>
<b>7 Configure TVHeadend:</b></br>
On your Ubuntu server browse <blockquote><i>http://127.0.0.1:9981</i></blockquote></br>
Use the username and password you set in Step 4</br>
</br>
Configuration -> Channel / EPG -> EPG Grabber Modules</br>
On the left side, highlight  'Internal: XMLTV: SmoothstreamsTV'</br>
On the right side, tick 'Enabled'</br>
Click 'Save'</br>
Configuration -> DVB Inputs -> Networks</br>
Click 'Add'</br>
Type = IPTV Automatic Network</br>
Network Name = SmoothstreamsTV</br>
URL = http://127.0.0.1:99/sstv/tvh.m3u8</br>
Maximum # input streams = 3</br>
Click Create</br>
Click Force Scan if it doesn't start scanned for muxes - wait for all the muxes to be scanned - there are 150 channels</br>
Go to the 'Services' tab</br>
Map Services -> Map all services</br>
</br>
Configuration -> Channel / EPG -> EPG Grabber Modules</br>
Click the button labeled 'Re-run Internal EPG Grabbers'</br>
**This will take a while to process** View the log down the bottom of the page. After it has run you should now see the channels in the EPG.</br>

<b>8 Restart sstvProxy:</b></br>
<blockquote><i>sudo /home/USERNAME/Desktop/sstv/sstvProxy</i></blockquote> <i>note no 'tvh' switch this time</i></p>""")

		html.write("<h2>Advanced Settings</h2>")
		html.write("""<p>

You can have as many or as few as you want and the file itself is optional. If you don't care for the option then don't even include it in the file, just delete it.</br></br>

There now exists an advanced settings example file on git. If this is in the same folder as the proxy it will detect it on launch and parse any settings that are within. </br></br>

Currently the accepted settings are:</br>
Custom ffmpeg locations "ffmpegloc":"C:\\ffmpeg\\bin\\ffmpeg.exe" (note the double slashes)</br>
Custom kodi control username "kodiuser":"string"</br>
Custom kodi control password "kodipass":"string"</br>
</br>
If you want to output a playlist that combines the SSTV channels with another playlist you already have then these options are for you:</br>
A url source for the above "extram3u8url":"url/string"</br>
A group name for the above, in order to filter between them in client "extram3u8name":"string"</br>
A file source for the above, url has priority though "extram3u8file":"path/string"</br>
</br>
If you want to output an EPG that combines the SSTV channels with another EPG you already have then:</br>
A url source for the above "extraxmlurl":"url/string"</br>
</br>
If you wish to use feed YAP into TVH and then TVH into Plex use the below:</br>
TVH url you use "tvhaddress": "127.0.0.1"</br>
username "tvhuser": ""</br>
password "tvhpass": ""</br>
</br>
If you want to override the EPG with your own one then:</br>
A url source for the epg "overridexml":"url/string"</p>""")
		html.write(footer)

		html.write("</body></html>\n")

def close_menu(restart):
	with open("./cache/close.html", "w") as html:
		html.write("""<html><head><title>YAP</title><meta charset="UTF-8">%s</head><body>\n""" % (style,))
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




def restart_program():
	os.system('cls' if os.name == 'nt' else 'clear')
	args = sys.argv[:]
	logger.info('Re-spawning %s' % ' '.join(args))
	#
	# args.insert(0, sys.executable)
	# if sys.platform == 'win32':
	# 	args = ['"%s"' % arg for arg in args]

	os.execl(sys.executable, *([sys.executable] + sys.argv))


# os.execv(sys.executable, args)


############################################################
# CLIENT <-> SSTV BRIDGE
############################################################
@app.route('/sstv/handle_data', methods=['POST'])
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
def landing_page():
	logger.info("Index was requested by %s", request.environ.get('REMOTE_ADDR'))
	create_menu()
	return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'index.html')


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


@app.route('/%s/<request_file>' % SERVER_PATH)
def bridge(request_file):
	global playlist, token, chan_map, kodiplaylist, tvhplaylist, fallback
	check_token()
	try:
		client = find_client(request.headers['User-Agent'])
	except:
		logger.debug("No user-agent provided by %s", request.environ.get('REMOTE_ADDR'))
		client = 'unk'

	if request_file.lower().endswith('.xspf'):
		playlist = build_xspf(SERVER_HOST, request_file)
		logger.info("XSPF playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		return Response(playlist, mimetype='application/xspf+xml')

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

	# return main menu
	elif request_file.lower().startswith('index'):
		logger.info("Index was requested by %s", request.environ.get('REMOTE_ADDR'))
		create_menu()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'index.html')

	# return settings menu
	elif request_file.lower().startswith('settings'):
		logger.info("Settings was requested by %s", request.environ.get('REMOTE_ADDR'))
		create_menu()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'settings.html')

	# return channels menu
	elif request_file.lower().startswith('channels'):
		logger.info("Channels was requested by %s", request.environ.get('REMOTE_ADDR'))
		create_menu()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'channels.html')

	# return howto menu
	elif request_file.lower().startswith('howto'):
		logger.info("Howto was requested by %s", request.environ.get('REMOTE_ADDR'))
		create_menu()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'howto.html')

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
				try:
					ss_url = create_channel_playlist(sanitized_channel, qual, strm, token[
					'hash'])  # hlsTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])
				except:
					ss_url = hlsurl

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
		jsonGuide1 = getJSON("iptv.json", "https://iptvguide.netlify.com/iptv.json",
		                     "https://fast-guide.smoothstreams.tv/altepg/feed1.json")
		jsonGuide2 = getJSON("tv.json", "https://iptvguide.netlify.com/tv.json",
		                     "https://fast-guide.smoothstreams.tv/altepg/feedall1.json")
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
	print("Static XSPF url is %s/static.xspf" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Dynamic XSPF url is %s/playlist.xspf" % urljoin(SERVER_HOST, SERVER_PATH))
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

	# debug causes it to load twice on initial startup and every time the script is saved, TODO disbale later
	try:
		app.run(host=LISTEN_IP, port=LISTEN_PORT, threaded=True, debug=False)
	except:
		os.system('cls' if os.name == 'nt' else 'clear')
		logger.exception("Proxy failed to launch, try another port")
	logger.info("Finished!")
