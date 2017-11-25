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
import webbrowser


try:
	from urlparse import urljoin
	import thread
except ImportError:
	from urllib.parse import urljoin
	import _thread

from flask import Flask, redirect, abort, request, Response, send_from_directory, jsonify, render_template, stream_with_context, url_for

app = Flask(__name__, static_url_path='')

__version__ = 1.44
#Changelog
#1.44 - Change of initial launch to use the gui, if not desired launch with 'python sstvproxy.py headless'. Added adv settings parsing see advancedsettings.json for example
#1.43 - Bugfix settings menu
#1.42 - External Playlist added, version check and download added
#1.41 - Bug fix and switch put on netwrok discovery
#1.40 - Settings menu added to /index.html
#1.37 - Network Discovery fixed hopefully
#1.36 - Two path bug fixes
#1.35 - Mac addon path fix and check
#1.34 - Fixed Plex Discovery, TVH file creation fix and addition of writing of genres and template files
#1.33 - Typo
#1.32 - Change server name dots to hyphens.
#1.31 - Tidying
#1.3 - EPG - Changed zap2it references to the channel number for better readability in clients that use that field as the channel name. As a result the epgs from both sources share the same convention. Playlist generators adjusted to suit.
#1.2 - TVH Completion and install
#1.1 - Refactoring and TVH inclusion
#1.0 - Initial post testing release
opener = requests.build_opener()
opener.addheaders = [('User-agent', 'YAP - %s - %s - %s' % (sys.argv[0], platform.system(), str(__version__)))]
requests.install_opener(opener)
type = ""
latestfile = "https://github.com/vorghahn/sstvProxy/blob/master/sstvProxy.py"
if not sys.argv[0].endswith('.py'):
	if platform.system() == 'Linux':
		type = "Linux/"
		latestfile = "https://github.com/vorghahn/sstvProxy/blob/master/Linux/sstvproxy"
	elif platform.system() == 'Windows':
		type  = "Windows/"
		latestfile = "https://github.com/vorghahn/sstvProxy/blob/master/Windows/sstvproxy.exe"
	elif platform.system() == 'Darwin':
		type = "Macintosh/"
		latestfile = "https://github.com/vorghahn/sstvProxy/blob/master/Macintosh/sstvproxy"
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

############################################################
# CONFIG
############################################################

#These are just defaults, place your settings in a file called proxysettings.json in the same directory

USER = ""
PASS = ""
SITE = "viewstvn"
SRVR = "dnaw2"
STRM = "hls"
QUAL = "1"
LISTEN_IP = "127.0.0.1"
LISTEN_PORT = 99
SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
SERVER_PATH = "sstv"
KODIPORT = 8080
EXTIP = "127.0.0.1"
EXT_HOST = "http://" + EXTIP + ":" + str(LISTEN_PORT)
KODIUSER = "kodi"
KODIPASS = ""
netdiscover = False

#LINUX/WINDOWS
if platform.system() == 'Linux':
	FFMPEGLOC = '/usr/bin/ffmpeg'
	if os.path.isdir(os.path.join(os.path.expanduser("~"), '.kodi','userdata','addon_data','pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), '.kodi','userdata','addon_data','pvr.iptvsimple')
	else: ADDONPATH = False
elif platform.system() == 'Windows':
	FFMPEGLOC = os.path.join('C:\FFMPEG' , 'bin', 'ffmpeg.exe')
	if os.path.isdir(os.path.join(os.path.expanduser("~"), 'AppData','Roaming','Kodi','userdata','addon_data','pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"), 'AppData','Roaming','Kodi','userdata','addon_data','pvr.iptvsimple')
	else: ADDONPATH = False
elif platform.system() == 'Darwin':
	FFMPEGLOC = ''
	if os.path.isdir(os.path.join(os.path.expanduser("~"),"Library","Application Support", 'Kodi','userdata','addon_data','pvr.iptvsimple')):
		ADDONPATH = os.path.join(os.path.expanduser("~"),"Library","Application Support", 'Kodi','userdata','addon_data','pvr.iptvsimple')
	else: ADDONPATH = False
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

providerList = [
	['Live247', 'view247'],
	['Mystreams/Usport', 'viewms'],
	['StarStreams', 'viewss'],
	['MMA SR+', 'viewmmasr'],
	['StreamTVnow', 'viewstvn'],
	['MMA-TV/MyShout', 'mmatv']
]

streamtype = ['hls','rtmp']

qualityList = [
	['HD', '1'],
	['HQ', '2'],
	['LQ', '3']
]

def adv_settings():
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]),'advancedsettings.json')):
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


def load_settings():
	global QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, SERVER_HOST, EXTIP, EXT_HOST
	try:
		logger.debug("Parsing settings")
		with open(os.path.join(os.path.dirname(sys.argv[0]),'proxysettings.json')) as jsonConfig:
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
			if "ip" in config and "port" in config:
				LISTEN_IP = config["ip"]
				LISTEN_PORT = config["port"]
				SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
				EXT_HOST = "http://" + EXTIP + ":" + str(LISTEN_PORT)
			#print("Using config file.")

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
				print(streamtype.index(i),i)
			config["stream"] = streamtype[int(input("Dynamic Stream Type? (HLS/RTMP)"))]
			os.system('cls' if os.name == 'nt' else 'clear')
			for i in qualityList:
				print(qualityList.index(i), qualityList[qualityList.index(i)][0])
			config["quality"] = int(qualityList[int(input("Stream quality?"))][1])
			os.system('cls' if os.name == 'nt' else 'clear')
			config["ip"] = input("Listening IP address?(ie recommend 127.0.0.1 for beginners)")
			config["port"] = int(input("and port?(ie 99, do not use 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			config["kodiport"] = int(input("Kodiport? (def is 8080)"))
			os.system('cls' if os.name == 'nt' else 'clear')
			config["externalip"] = input("External IP?")
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
			SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
			EXT_HOST = "http://" + EXTIP + ":" + str(LISTEN_PORT)
			with open(os.path.join(os.path.dirname(sys.argv[0]),'proxysettings.json'), 'w') as fp:
				dump(config, fp)
		else:
			create_menu()
			url = os.path.join(os.path.dirname(sys.argv[0]),'cache','settings.html')
			webbrowser.open(url, new=2)
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
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Rotating Log Files
if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), 'cache')):
	os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), 'cache'))
file_handler = RotatingFileHandler(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'status.log'), maxBytes=1024 * 1024 * 2,
								   backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)


############################################################
# INSTALL
############################################################

def installer():
	if os.path.isfile(os.path.join('/usr','bin','tv_find_grabbers')):
		writetvGrabFile()
		os.chmod('/usr/bin/tv_grab_sstv', 0o777)
		proc = subprocess.Popen( "/usr/bin/tv_find_grabbers" )
	if os.path.isdir(ADDONPATH):
		writesettings()
		writegenres()
	if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]),'Templates')):
		os.mkdir(os.path.join(os.path.dirname(sys.argv[0]),'Templates'))
	writetemplate()


def writetvGrabFile():
	f = open(os.path.join('/usr','bin', 'tv_grab_sstv'), 'w')
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
fi''' % (SERVER_HOST,SERVER_PATH)
	f.write(tvGrabFile)
	f.close()


#lazy install, low priority
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
</settings>""" % (SERVER_HOST,SERVER_PATH,SERVER_HOST,SERVER_PATH)
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
	f = open(os.path.join(os.path.dirname(sys.argv[0]),'Templates', 'device.xml'), 'w')
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
	#download icons to cache
	logger.debug("Downloading icons")
	icontemplate = 'https://guide.smoothstreams.tv/assets/images/channels/{0}.png'
	#create blank icon
	requests.urlretrieve(icontemplate.format(150), os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'empty.png'))
	for i in range(1,channum+1):
		name = str(i) + '.png'
		try:
			requests.urlretrieve(icontemplate.format(i), os.path.join(os.path.dirname(sys.argv[0]), 'cache', name))
		except:
			continue
			#logger.debug("No icon for channel:%s"% i)
	logger.debug("Icon download completed.")


############################################################
# EPG
############################################################


def dl_epg(source=1):
	global chan_map
	#download epg xml
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml')):
		existing = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml')
		cur_utc_hr = datetime.utcnow().replace(microsecond=0,second=0,minute=0).hour
		target_utc_hr = (cur_utc_hr//3)*3
		target_utc_datetime = datetime.utcnow().replace(microsecond=0,second=0,minute=0, hour=target_utc_hr)
		print("utc time is: %s,    utc target time is: %s,    file time is: %s" % (datetime.utcnow(), target_utc_datetime, datetime.utcfromtimestamp(os.stat(existing).st_mtime)))
		if os.path.isfile(existing) and os.stat(existing).st_mtime > target_utc_datetime.timestamp():
			logger.debug("Skipping download of epg")
			return
	if source == 1:
		logger.debug("Downloading epg")
		requests.urlretrieve("https://sstv.fog.pt/epg/xmltv5.xml.gz", os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml.gz'))
		unzipped = gzip.open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml.gz'))
	else:
		logger.debug("Downloading sstv epg")
		requests.urlretrieve("http://speed.guide.smoothstreams.tv/feed.xml", os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml'))
		unzipped = open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'rawepg.xml'))
	#try to categorise the sports events
	tree = ET.parse(unzipped)
	root = tree.getroot()
	changelist={}
	#remove fogs xmltv channel names for readability in PLex Live
	if source == 1:
		for a in tree.iterfind('channel'):
			b = a.find('display-name')
			newname = [chan_map[x].channum for x in range(len(chan_map)+1) if x!= 0 and chan_map[x].epg == a.attrib['id'] and chan_map[x].channame == b.text]
			if len(newname) > 1:
				logger.debug("EPG rename conflict")
				print(a.attrib['id'], newname)
			else:
				newname = newname[0]
				changelist[a.attrib['id']] = newname
			a.attrib['id'] = newname
	for a in tree.iterfind('programme'):
		if source == 1:
			a.attrib['channel'] = changelist[a.attrib['channel']]
		for b in a.findall('title'):
			if source == 2:
				ET.SubElement(a, 'category')
			c = a.find('category')
			c.text="Sports"
			if 'nba' in b.text.lower() or 'nba' in b.text.lower() or 'ncaam' in b.text.lower():
				c.text="Basketball"
			elif 'nfl' in b.text.lower() or 'football' in b.text.lower() or 'american football' in b.text.lower() or 'ncaaf' in b.text.lower() or 'cfb' in b.text.lower():
				c.text="Football"
			elif 'epl' in b.text.lower() or 'efl' in b.text.lower() or 'soccer' in b.text.lower() or 'ucl' in b.text.lower() or 'mls' in b.text.lower() or 'uefa' in b.text.lower() or 'fifa' in b.text.lower() or 'fc' in b.text.lower() or 'la liga' in b.text.lower() or 'serie a' in b.text.lower() or 'wcq' in b.text.lower():
				c.text="Soccer"
			elif 'rugby' in b.text.lower() or 'nrl' in b.text.lower() or 'afl' in b.text.lower():
				c.text="Rugby"
			elif 'cricket' in b.text.lower() or 't20' in b.text.lower():
				c.text="Cricket"
			elif 'tennis' in b.text.lower() or 'squash' in b.text.lower() or 'atp' in b.text.lower():
				c.text="Tennis/Squash"
			elif 'f1' in b.text.lower() or 'nascar' in b.text.lower() or 'motogp' in b.text.lower() or 'racing' in b.text.lower():
				c.text="Motor Sport"
			elif 'golf' in b.text.lower() or 'pga' in b.text.lower():
				c.text="Golf"
			elif 'boxing' in b.text.lower() or 'mma' in b.text.lower() or 'ufc' in b.text.lower() or 'wrestling' in b.text.lower() or 'wwe' in b.text.lower():
				c.text="Martial Sports"
			elif 'hockey' in b.text.lower() or 'nhl' in b.text.lower() or 'ice hockey' in b.text.lower():
				c.text="Ice Hockey"
			elif 'baseball' in b.text.lower() or 'mlb' in b.text.lower() or 'beisbol' in b.text.lower() or 'minor league' in b.text.lower():
				c.text="Baseball"
			#c = a.find('category')
			#if c.text == 'Sports':
			#    print(b.text)
	tree.write(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml'))
	#add xml header to file for Kodi support
	with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml'), 'r+') as f:
		content = f.read()
		staticinfo = '''<channel id="static_refresh"><display-name lang="en">Static Refresh</display-name><icon src="http://speed.guide.smoothstreams.tv/assets/images/channels/150.png" /></channel><programme channel="static_refresh" start="20170118213000 +0000" stop="20201118233000 +0000"><title lang="us">Press to refresh rtmp channels</title><desc lang="en">Select this channel in order to refresh the RTMP playlist. Only use from the channels list and NOT the guide page. Required every 4hrs.</desc><category lang="us">Other</category><episode-num system="">1</episode-num></programme></tv>'''
		content = content[:-5] + staticinfo
		f.seek(0, 0)
		f.write('<?xml version="1.0" encoding="UTF-8"?>'.rstrip('\r\n') + content)


#started to create epg based off of the json but not needed
def dl_sstv_epg():
	#download epg xml
	if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml')):
		existing = os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'epg.xml')
		cur_utc_hr = datetime.utcnow().replace(microsecond=0,second=0,minute=0).hour
		target_utc_hr = (cur_utc_hr//3)*3
		target_utc_datetime = datetime.utcnow().replace(microsecond=0,second=0,minute=0, hour=target_utc_hr)
		print("utc time is: %s,    utc target time is: %s,    file time is: %s" % (datetime.utcnow(), target_utc_datetime, datetime.utcfromtimestamp(os.stat(existing).st_mtime)))
		if os.path.isfile(existing) and os.stat(existing).st_mtime > target_utc_datetime.timestamp():
			logger.debug("Skipping download of epg")
			#return
	logger.debug("Downloading sstv epg")
	url = "https://speed.guide.smoothstreams.tv/feed-new.json"
	jsonepg = json.loads(requests.urlopen(url).read().decode("utf-8"))
	xml = json2xml(jsonepg)
	f = open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'sstvepg.xml'), 'w')
	f.write(xml)
	f.close()


def json2xml(json_obj, line_padding=""):
	result_list = list()

	json_obj_type = type(json_obj)

	if json_obj_type is list:
		for sub_elem in json_obj:
			result_list.append(json2xml(sub_elem, line_padding))

		return "\n".join(result_list)

	if json_obj_type is dict:
		for tag_name in json_obj:
			sub_obj = json_obj[tag_name]
			result_list.append("%s<%s>" % (line_padding, tag_name))
			result_list.append(json2xml(sub_obj, "\t" + line_padding))
			result_list.append("%s</%s>" % (line_padding, tag_name))

		return "\n".join(result_list)

	return "%s%s" % (line_padding, json_obj)


############################################################
# SSTV
############################################################


def get_auth_token(user, passwd, site):
	data = json.loads(requests.urlopen('http://auth.SmoothStreams.tv/hash_api.php?username=%s&password=%s&site=%s' % (user,passwd,site)).read().decode("utf-8"))
	if 'hash' not in data or 'valid' not in data:
		logger.error("There was no hash auth token returned from auth.SmoothStreams.tv...")
		return
	else:
		token['hash'] = data['hash']
		token['expires'] = (datetime.now() + timedelta(minutes=data['valid'])).strftime("%Y-%m-%d %H:%M:%S.%f")
		logger.info("Retrieved token %r, expires at %s", token['hash'], token['expires'])
		return


def check_token():
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
		#print(item)
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
		#print(item)
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
	#standard dynamic playlist
	global chan_map

	# build playlist using the data we have
	new_playlist = "#EXTM3U\n"
	for pos in range(1, len(chan_map) + 1):
		# build channel url
		url = "{0}/playlist.m3u8?ch={1}&strm={2}&qual={3}"
		rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
		urlformatted = url.format(SERVER_PATH, chan_map[pos].channum,STRM, QUAL)
		channel_url = urljoin(host,urlformatted)
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, host, SERVER_PATH,  chan_map[pos].channum, chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % channel_url

		except:
			logger.exception("Exception while updating playlist: ")
	logger.info("Built Dynamic playlist")

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
		#Used to support HLS HTTPS requests
		template = 'https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/chunks'
		file = file.replace('chunks', template.format(SRVR, SITE, sanitized_channel, qual))
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'playlist.m3u8'), 'r+') as f:
			f.write(file)
		return file
	else:
		#not used currently
		template = 'http://{0}.smoothstreams.tv:9100/{1}/ch{2}q{3}.stream/chunks'
		file = '#EXTM3U\n#EXTINF:' + file[43:110] + "\n" + rtmp_url
		#with open(os.path.join(os.path.dirname(sys.argv[0]), 'cache', 'playlist.m3u8'), 'r+') as f:
		#    f.write(file)
		return rtmp_url

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
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, name, SERVER_HOST, SERVER_PATH,  name, chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % channel_url

		except:
			logger.exception("Exception while updating playlist: ")
	logger.info("Built TVH playlist")

	return new_playlist


############################################################
# PLEX Live
############################################################


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
		'LineupURL': '%s/lineup.json' % (SERVER_HOST + "/" + SERVER_PATH)
	}


def discover():
	return jsonify(discoverData)


def status():
	return jsonify({
		'ScanInProgress': 0,
		'ScanPossible': 1,
		'Source': "Cable",
		'SourceList': ['Cable']
	})


def lineup(chan_map):
	lineup = []

	for c in range(1, len(chan_map) + 1):
		template = "{0}/{1}/auto/v{2}"
		url = template.format(SERVER_HOST, SERVER_PATH, chan_map[c].channum)
		lineup.append({'GuideNumber': str(chan_map[c].channum),
						   'GuideName': chan_map[c].channame,
						   'URL': url
						   })

	return jsonify(lineup)


def lineup_post():
	return ''

def device():
	return render_template('device.xml',data = discoverData),{'Content-Type': 'application/xml'}


#PLEX DVR EPG from here
# Where the script looks for an EPG database
dbpat = os.path.join("\\\SERVER","Users","blindman","AppData","Local","Plex Media Server","Plug-in Support","Databases","tv.plex.providers.epg.xmltv-c76f26d4-d656-4d92-9771-1f8da949c015.db")

# Change this to change the style of the web page generated
style = """
<style type="text/css">
	body { max-width: 60em; background-color: white; color: black; }
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
</style>
"""


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
				html.write("<p>%s &ndash; %s: <b>%s</b>\n" % # (%d)\n" %
						   (start, end, row["title"]))#, row["year"]))

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
		print("Found no database matching %s" % dbpat)
	elif len(dbs) > 1:
		print("Found multiple databases matching %s" % dbpat)
	else:
		dbfile = dbs[0]
		if not os.access(dbfile, os.W_OK):
			print("Database file not writable (required for queries): %s" % dbfile)
		else:
			create_list(dbfile, epgsummaries, epggenres, epgorig)
#PLEX DVR EPG Ends


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

ignorelist = ['127.0.0.1'] # the tvheadend ip address(es), tvheadend crashes when it discovers the tvhproxy (TODO: Fix this)


def retrieveTypeAndPayload(packet):
	header = packet[:4]
	checksum = packet[-4:]
	payload = packet[4:-4]

	packetType, payloadLength = struct.unpack('>HH',header)
	if payloadLength != len(payload):
		print('Bad packet payload length')
		return False

	if checksum != struct.pack('>I', cksum(header + payload)):
		print('Bad checksum')
		return False

	return (packetType, payload)

def createPacket(packetType, payload):
	header = struct.pack('>HH', packetType, len(payload))
	data = header + payload
	checksum = cksum(data)
	packet = data + struct.pack('>I', checksum)

	return packet

def processPacket(packet, client, logPrefix = ''):
	packetType, requestPayload = retrieveTypeAndPayload(packet)

	if packetType == HDHOMERUN_TYPE_DISCOVER_REQ:
		logger.debug('Discovery request received from ' + client[0])
		responsePayload = struct.pack('>BBI', HDHOMERUN_TAG_DEVICE_TYPE, 0x04, HDHOMERUN_DEVICE_TYPE_TUNER) #Device Type Filter (tuner)
		responsePayload += struct.pack('>BBI', HDHOMERUN_TAG_DEVICE_ID, 0x04, int('12345678', 16)) #Device ID Filter (any)
		responsePayload += struct.pack('>BB', HDHOMERUN_TAG_GETSET_NAME, len(SERVER_HOST)) + str.encode(SERVER_HOST) #Device ID Filter (any)
		responsePayload += struct.pack('>BBB', HDHOMERUN_TAG_TUNER_COUNT, 0x01, 6) #Device ID Filter (any)

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
			tag, length = struct.unpack('>BB',header)
			# TODO: If the length is larger than 127 the following bit is also needed to determine length
			if length > 127:
				logger.debug('Unable to determine tag length, the correct way to determine a length larger than 127 must still be implemented.')
				return False
			# TODO: Implement other tags
			if tag == HDHOMERUN_TAG_GETSET_NAME:
				getSetName = struct.unpack('>{0}'.format(length),payloadIO.read(length))[0]
			if tag == HDHOMERUN_TAG_GETSET_VALUE:
				getSetValue = struct.unpack('>{0}'.format(length),payloadIO.read(length))[0]

		if getSetName is None:
			return False
		else:
			responsePayload = struct.pack('>BB{0}'.format(len(getSetName)), HDHOMERUN_TAG_GETSET_NAME, len(getSetName), getSetName)

			if getSetValue is not None:
				responsePayload += struct.pack('>BB{0}'.format(len(getSetValue)), HDHOMERUN_TAG_GETSET_VALUE, len(getSetValue), getSetValue)

			return createPacket(HDHOMERUN_TYPE_GETSET_RPY, responsePayload)

	return False

def tcpServer():
	logPrefix = 'TCP Server - '
	logger.debug('Starting tcp server')
	controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	controlSocket.bind((LISTEN_IP, HDHOMERUN_CONTROL_TCP_PORT))
	controlSocket.listen(1)

	logger.debug('Listening...')
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

	logger.debug('Stopping server')
	controlSocket.close()

def udpServer():
	logPrefix = 'UDP Server - '
	logger.debug('Starting udp server')
	discoverySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	discoverySocket.bind(('0.0.0.0', HDHOMERUN_DISCOVER_UDP_PORT))
	logger.debug('Listening...')
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

	discoverySocket.close()


############################################################
# Kodi
############################################################


def build_kodi_playlist():
	#kodi playlist contains two copies of channels, first is dynmaic HLS and the second is static rtmp
	global chan_map
	# build playlist using the data we have
	new_playlist = "#EXTM3U\n"
	for pos in range(1, len(chan_map) + 1):
		# build channel url
		url = "{0}/playlist.m3u8?ch={1}&strm={2}&qual={3}"
		rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
		urlformatted = url.format(SERVER_PATH, chan_map[pos].channum,'hls', QUAL)
		channel_url = urljoin(SERVER_HOST,urlformatted)
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s" group-title="Dynamic",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH,  chan_map[pos].channum, chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % channel_url
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s" group-title="Static RTMP",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH, chan_map[pos].channum, chan_map[pos].channum,
				chan_map[pos].channame)
			new_playlist += '%s\n' % rtmpTemplate.format(SRVR, SITE, "{:02}".format(pos), QUAL, token['hash'])
		except:
			logger.exception("Exception while updating playlist: ")
	new_playlist += '#EXTINF:-1 tvg-id="static_refresh" tvg-name="Static Refresh" tvg-logo="%s/%s/empty.png" channel-id="0" group-title="Static RTMP",Static Refresh\n' % (
		SERVER_HOST, SERVER_PATH)
	new_playlist += '%s/%s/refresh.m3u8\n' % (SERVER_HOST, SERVER_PATH)
	logger.info("Built Kodi playlist")

	if ADDONPATH and os.path.isdir(ADDONPATH):
		#lazy install, low priority tbh
		tree = ET.parse(os.path.join(ADDONPATH, 'settings.xml'))
		root = tree.getroot()
		for child in root:
			if child.attrib['id'] == 'epgUrl':
				child.attrib['value'] = '%s/%s/epg.xml' % (SERVER_HOST, SERVER_PATH)
			elif child.attrib['id'] == 'm3uUrl':
				child.attrib['value'] = '%s/%s/kodi.m3u8' % (SERVER_HOST, SERVER_PATH)
			elif child.attrib['id'] == 'epgPathType':
				child.attrib['value'] = '1'
			elif child.attrib['id'] == 'm3uPathType':
				child.attrib['value'] = '1'
		tree.write(os.path.join(ADDONPATH, 'settings.xml'))
	return new_playlist


def rescan_channels():
	credentials = str.encode(KODIUSER+':'+KODIPASS)
	encoded_credentials = base64.b64encode(credentials)
	authorization = b'Basic ' + encoded_credentials
	apiheaders = { 'Content-Type': 'application/json', 'Authorization': authorization }
	apidata = {"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":"toggle"},"id":1}
	apiurl = 'http://%s:%s/jsonrpc' % (request.environ.get('REMOTE_ADDR'), KODIPORT)
	json_data = json.dumps(apidata)
	post_data = json_data.encode('utf-8')
	apirequest = requests.Request(apiurl, post_data, apiheaders)
	#has to happen twice to toggle off then back on
	result = requests.urlopen(apirequest)
	result = requests.urlopen(apirequest)
	logger.info("Forcing Kodi to rescan, result:%s " % result.read())


############################################################
# Html
############################################################


# Change this to change the style of the web page generated
style = """
<style type="text/css">
	body { max-width: 20em; background-color: white; color: black; }
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
</style>
"""


def create_menu():
	with open("./cache/settings.html", "w") as html:
		html.write("""<html>
		<head>
		<meta charset="UTF-8">
		%s
		</head>
		<body>\n""" % (style,))
		html.write('<form action="%s/%s/handle_data" method="post">' % (SERVER_HOST, SERVER_PATH))
		html.write("<h1>YAP Settings</h1>")

		channelmap = {}
		chanindex = 0
		list = ["Username","Password","Quality","Stream","Server","Service","IP","Port","Kodiport","ExternalIP"]
		html.write('<table width="300" border="2">')
		for setting in list:
			if setting.lower() == 'service':
				html.write('<tr><td>Service:</td><td><select name="Service" size="1">')
				for option in providerList:
					html.write('<option value="%s"%s>%s</option>' % (option[0],' selected' if SITE == option[1] else "", option[0]))
				html.write('</select></td></tr>')
			elif setting.lower() == 'server':
				html.write('<tr><td>Server:</td><td><select name="Server" size="1">')
				for option in serverList:
					html.write('<option value="%s"%s>%s</option>' % (option[0],' selected' if SRVR == option[1] else "", option[0]))
				html.write('</select></td></tr>')
			elif setting.lower() == 'stream':
				html.write('<tr><td>Stream:</td><td><select name="Stream" size="1">')
				for option in streamtype:
					html.write('<option value="%s"%s>%s</option>' % (option,' selected' if STRM == option else "", option))
				html.write('</select></td></tr>')
			elif setting.lower() == 'quality':
				html.write('<tr><td>Quality:</td><td><select name="Quality" size="1">')
				for option in qualityList:
					html.write('<option value="%s"%s>%s</option>' % (option[0],' selected' if QUAL == option[1] else "", option[0]))
				html.write('</select></td></tr>')
			elif setting.lower() == 'password':
				html.write('<tr><td>%s:</td><td><input name="%s" type="Password" value="%s"></td></tr>'% (setting, setting, PASS))
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
				html.write('<tr><td>%s:</td><td><input name="%s" type="text" value="%s"></td></tr>'% (setting, setting, val))
		html.write('</table>')
		html.write('<input type="submit"  value="Submit">')
		html.write('</form>')
		html.write("</body></html>\n")
		
		
def close_menu():
	with open("./cache/close.html", "w") as html:
		html.write("""<html><head><meta charset="UTF-8">%s</head><body>\n""" % (style,))
		html.write("<h1>Data Saved</h1>")
		html.write("</body></html>\n")
		
		
############################################################
# CLIENT <-> SSTV BRIDGE
############################################################
@app.route('/sstv/handle_data', methods=['POST'])
def handle_data():
	global playlist, kodiplaylist,QUAL,USER,PASS,SRVR,SITE,STRM,KODIPORT,LISTEN_IP,LISTEN_PORT,EXTIP,EXT_HOST,SERVER_HOST
	inc_data = request.form
	config = {}
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
			config["quality"] = int(sub[1])
	config["ip"] = inc_data['IP']
	config["port"] = int(inc_data['Port'])
	config["kodiport"] = int(inc_data['Kodiport'])
	config["externalip"] = inc_data['ExternalIP']
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
	EXT_HOST = "http://" + EXTIP + ":" + str(LISTEN_PORT)
	SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
	with open(os.path.join(os.path.dirname(sys.argv[0]),'proxysettings.json'), 'w') as fp:
		dump(config, fp)
	close_menu()
	check_token()
	playlist = build_playlist(SERVER_HOST)
	kodiplaylist = build_kodi_playlist()
	print(SRVR)
	return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'close.html')


@app.route('/<request_file>')
def index(request_file):
	logger.info("%s requested by %s" % (request_file, request.environ.get('REMOTE_ADDR')))
	if request_file.lower() == 'lineup_status.json':
		return status()
	elif request_file.lower() == 'discover.json':
		return discover()
	elif request_file.lower() == 'lineup.json':
		return lineup(chan_map)
	elif request_file.lower() == 'lineup.post':
		return lineup_post()
	#logger.debug(request.headers)
	elif request_file.lower() == 'device.xml':
		return device()
	elif request_file.lower() == 'favicon.ico':
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')


@app.route('/%s/<request_file>' % SERVER_PATH)
def bridge(request_file):
	global playlist, token, chan_map, kodiplaylist, tvhplaylist

	#return epg
	if request_file.lower().startswith('epg.'):
		logger.info("EPG was requested by %s", request.environ.get('REMOTE_ADDR'))
		if not fallback:
			dl_epg()
		else:
			logger.info("EPG download failed. Trying SSTV.")
			dl_epg(2)
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'epg.xml')

	#return icons
	elif request_file.lower().endswith('.png'):
		try:
			return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), request_file)
		except:
			return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')
			
	elif request_file.lower() == 'favicon.ico':
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')

	#return html epg guide based off of plex live
	elif request_file.lower().startswith('guide'):
		epgguide()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'guide.html')

	#return settings menu
	elif request_file.lower().startswith('index'):
		#try:
		create_menu()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'settings.html')
		
	#kodi static refresh
	elif request_file.lower().startswith('refresh'):
		#kodi force rescan 423-434
		logger.info("Refresh was requested by %s", request.environ.get('REMOTE_ADDR'))
		load_token()
		check_token()
		rescan_channels()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')

	#returns kodi playlist
	elif request_file.lower().startswith('kodi'):
		kodiplaylist = build_kodi_playlist()
		logger.info("Kodi channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		logger.info("Sending playlist to %s", request.environ.get('REMOTE_ADDR'))
		return Response(kodiplaylist, mimetype='application/x-mpegURL')
		
	#returns external playlist
	elif request_file.lower().startswith('external'):
		extplaylist = build_playlist(EXT_HOST)
		logger.info("External channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		logger.info("Sending playlist to %s", request.environ.get('REMOTE_ADDR'))
		return Response(extplaylist, mimetype='application/x-mpegURL')

	#returns tvh playlist
	elif request_file.lower().startswith('tvh'):
		tvhplaylist = build_tvh_playlist()
		logger.info("TVH channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
		logger.info("Sending playlist to %s", request.environ.get('REMOTE_ADDR'))
		return Response(tvhplaylist, mimetype='application/x-mpegURL')

	elif request_file.lower() == 'playlist.m3u8':
		#returning Dynamic channels
		if request.args.get('ch'):
			sanitized_channel = ("0%d" % int(request.args.get('ch'))) if int(
				request.args.get('ch')) < 10 else request.args.get('ch')
			check_token()

			qual = '1'
			if request.args.get('qual') and int(sanitized_channel) <= 60:
				qual = request.args.get('qual')
			if request.args.get('strm') and request.args.get('strm') == 'rtmp':
				strm = 'rtmp'
				rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
				ss_url = rtmpTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])
			else:
				strm = 'hls'
				hlsTemplate = 'https://{0}.smoothstreams.tv:443/{1}/ch{2}q{3}.stream/chunks.m3u8?wmsAuthSign={4}=='
				ss_url = create_channel_playlist(sanitized_channel, qual, strm, token['hash'])#hlsTemplate.format(SRVR, SITE, sanitized_channel, qual, token['hash'])

			response = redirect(ss_url, code=302)
			headers = dict(response.headers)
			headers.update({'Content-Type': 'application/x-mpegURL', "Access-Control-Allow-Origin": "*"})
			response.headers = headers
			logger.info("Channel %s playlist was requested by %s", sanitized_channel,request.environ.get('REMOTE_ADDR'))
			#useful for debugging
			logger.debug("URL returned: %s" % ss_url)
			if strm == 'rtmp':
				return response
			else:
				#some players are having issues with http/https redirects
				return ss_url
			#return redirect(ss_url, code=302)
			#return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'playlist.m3u8')

		#returning dynamic playlist
		else:
			playlist = build_playlist(SERVER_HOST)
			logger.info("All channels playlist was requested by %s", request.environ.get('REMOTE_ADDR'))
			logger.info("Sending playlist to %s", request.environ.get('REMOTE_ADDR'))
			return Response(playlist, mimetype='application/x-mpegURL')
	#HDHomeRun emulated json files for Plex Live tv.
	elif request_file.lower() == 'lineup_status.json':
		return status()
	elif request_file.lower() == 'discover.json':
		return discover()
	elif request_file.lower() == 'lineup.json':
		return lineup(chan_map)
	elif request_file.lower() == 'lineup.post':
		return lineup_post()
	elif request_file.lower() == 'device.xml':
		return device()
	else:
		logger.info("Unknown requested %r by %s", request_file, request.environ.get('REMOTE_ADDR'))
		abort(404, "Unknown request")


@app.route('/%s/auto/<request_file>' % SERVER_PATH)
#returns a piped stream, used for TVH/Plex Live TV
def auto(request_file):
	print("starting pipe function")
	check_token()
	channel = request_file.replace("v","")
	logger.info("Channel %s playlist was requested by %s", channel,
			request.environ.get('REMOTE_ADDR'))
	sanitized_channel = ("0%d" % int(channel)) if int(channel) < 10 else channel
	sanitized_qual = 1 if int(channel) > 60 else QUAL
	template = "http://{0}.smoothstreams.tv:9100/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}"
	url =  template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	print("sanitized_channel: %s sanitized_qual: %s" % (sanitized_channel,sanitized_qual))
	print(url)
	try:
		urllib.request.urlopen(url, timeout=2).getcode()
	except timeout:
		#special arg for tricking tvh into saving every channel first time
		print("timeout")
		sanitized_channel = '01'
		sanitized_qual = '3'
		url =  template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	except:
		print("except")
		sanitized_channel = '01'
		sanitized_qual = '3'
		url =  template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	print(url)
	import subprocess

	def generate():
		print("starting generate function")
		cmdline= list()
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
		print(cmdline)
		FNULL = open(os.devnull, 'w')
		proc= subprocess.Popen( cmdline, stdout=subprocess.PIPE, stderr=FNULL )
		print("pipe started")
		try:
			f= proc.stdout
			byte = f.read(512)
			while byte:
				yield byte
				byte = f.read(512)

		finally:
			proc.kill()

	return Response(response=generate(),status=200,mimetype='video/mp2t',headers={'Access-Control-Allow-Origin': '*', "Content-Type":"video/mp2t","Content-Disposition":"inline","Content-Transfer-Enconding":"binary"})


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
			#cannot get response from fog, resorting to fallback
			fallback = True
			chan_map = build_channel_map_sstv()
		playlist = build_playlist(SERVER_HOST)
		kodiplaylist = build_kodi_playlist()
		tvhplaylist = build_tvh_playlist()
		#Download icons, runs in sep thread, takes ~1min
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

	print("\n##############################################################")
	print("Change your settings at %s/index.html" %  urljoin(SERVER_HOST, SERVER_PATH))
	print("m3u8 url is %s/playlist.m3u8" %  urljoin(SERVER_HOST, SERVER_PATH))
	print("kodi m3u8 url is %s/kodi.m3u8" %  urljoin(SERVER_HOST, SERVER_PATH))
	print("EPG url is %s/epg.xml" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Plex Live TV url is %s" % urljoin(SERVER_HOST, SERVER_PATH))
	print("TVHeadend network url is %s/tvh.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("External m3u8 url is %s/external.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("##############################################################\n")
	logger.info("Listening on %s:%d at %s/", LISTEN_IP, LISTEN_PORT, urljoin(SERVER_HOST, SERVER_PATH))
	if __version__ < latest_ver:
		logger.info("Your version (%s%s) is out of date, the latest is %s, which has now be downloaded for you into the 'updates' subdirectory." % (type, __version__, latest_ver))
		newfilename = ntpath.basename(latestfile)
		if not os.path.isdir(os.path.join(os.path.dirname(sys.argv[0]), 'updates')):
			os.mkdir(os.path.join(os.path.dirname(sys.argv[0]), 'updates'))
		requests.urlretrieve(latestfile, os.path.join(os.path.dirname(sys.argv[0]), 'updates', newfilename))
	else:
		logger.info("Your version (%s) is up to date." % (__version__))
	if netdiscover:
		try:
			a = threading.Thread(target=udpServer)
			a.setDaemon(True)
			a.start()
		except (KeyboardInterrupt, SystemExit):
			sys.exit()
	#debug causes it to load twice on initial startup and every time the script is saved, TODO disbale later
	app.run(host=LISTEN_IP, port=LISTEN_PORT, threaded=True, debug=False)
	logger.info("Finished!")
