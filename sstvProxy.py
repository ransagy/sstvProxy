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


try:
	from urlparse import urljoin
	import thread
except ImportError:
	from urllib.parse import urljoin
	import _thread

from flask import Flask, redirect, abort, request, Response, send_from_directory, jsonify, render_template, stream_with_context

app = Flask(__name__, static_url_path='')

__version__ = 1.31
#Changelog
#1.31 - Tidying
#1.3 - EPG - Changed zap2it references to the channel number for better readability in clients that use that field as the channel name. As a result the epgs from both sources share the same convention. Playlist generators adjusted to suit.
#1.2 - TVH Completion and install
#1.1 - Refactoring and TVH inclusion
#1.0 - Initial post testing release

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

#LINUX/WINDOWS
if platform.system() == 'Linux':
	FFMPEGLOC = '/usr/bin/ffmpeg'
	ADDONPATH = os.path.join(os.path.expanduser("~"), '.kodi','userdata','addon_data','pvr.iptvsimple')
elif platform.system() == 'Windows':
	FFMPEGLOC = os.path.join('C:\FFMPEG' , 'bin', 'ffmpeg.exe')
	ADDONPATH = os.path.join(os.path.expanduser("~"), 'AppData','Roaming','Kodi','userdata','addon_data','pvr.iptvsimple')
elif platform.system() == 'Darwin':
	FFMPEGLOC = ''
	ADDONPATH = os.path.join(os.path.expanduser("~"),"Library","Application Support", '.kodi','userdata','addon_data','pvr.iptvsimple')


############################################################
# INSTALL
############################################################

def installer():
	if os.path.isfile(os.path.join('/usr','bin','tv_find_grabbers')):
		writetvGrabFile()
		os.chmod('/usr/bin/tv_grab_sstv', 0o777)
		proc = subprocess.Popen( "/usr/bin/tv_find_grabbers" )
	if os.path.isfile(ADDONPATH):
		writetvGrabFile()

def writetvGrabFile():
	f = open(os.path.join('/usr','bin', 'tv_grab_sstv'), 'w')
	tvGrabFile = '''
		#!/bin/sh
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
############################################################
# INIT
############################################################

serverList = [
	[' EU-Mix', 'deu'],
	['    DE-Frankfurt', 'deu.de'],
	['    NL-Mix', 'deu.nl'],
	['    NL-1', 'deu.nl1'],
	['    NL-2', 'deu.nl2'],
	['    NL-3 Ams', 'deu.nl3'],
	['    NL-4 Breda', 'deu.nl4'],
	['    NL-5 Enschede', 'deu.nl5'],
	['    UK-Mix', 'deu.uk'],
	['    UK-London1', 'deu.uk1'],
	['    UK-London2', 'deu.uk2'],
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
try:
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
		if "ip" in config and "port" in config:
			LISTEN_IP = config["ip"]
			LISTEN_PORT = config["port"]
			SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
		#print("Using config file.")
except:
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
	config["quality"] = int(input("Quality(1,2,3)"))
	os.system('cls' if os.name == 'nt' else 'clear')
	config["ip"] = input("Listening IP address?(ie recommend 127.0.0.1 for beginners)")
	config["port"] = int(input("and port?(ie 99, do not use 8080)"))
	os.system('cls' if os.name == 'nt' else 'clear')
	config["kodiport"] = int(input("Kodiport? (def is 8080)"))
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
	SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
	with open(os.path.join(os.path.dirname(sys.argv[0]),'proxysettings.json'), 'w') as fp:
		dump(config, fp)
	installer()



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
		exit(1)
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


def build_playlist():
	#standard dynamic playlist
	global chan_map

	# build playlist using the data we have
	new_playlist = "#EXTM3U\n"
	for pos in range(1, len(chan_map) + 1):
		# build channel url
		url = "{0}/playlist.m3u8?ch={1}&strm={2}&qual={3}"
		rtmpTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}/ch{2}q{3}.stream?wmsAuthSign={4}'
		urlformatted = url.format(SERVER_PATH, chan_map[pos].channum,STRM, QUAL)
		channel_url = urljoin(SERVER_HOST,urlformatted)
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH,  chan_map[pos].channum, chan_map[pos].channum,
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
			tmp_playlist = build_playlist()
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
		# build playlist entry
		try:
			new_playlist += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s/%s/%s.png" channel-id="%s",%s\n' % (
				chan_map[pos].channum, chan_map[pos].channame, SERVER_HOST, SERVER_PATH,  chan_map[pos].channum, chan_map[pos].channum,
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

#TODO
#not working atm, unsure of it's need
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

	if os.path.isdir(ADDONPATH):
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
	credentials = b'kodi:'
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
# CLIENT <-> SSTV BRIDGE
############################################################


@app.route('/')
@app.route('/%s/' % SERVER_PATH)
@app.route('/%s/discover.json' % SERVER_PATH)
def disc():
	logger.debug(request.headers)
	return discover()

@app.route('/')
@app.route('/%s/' % SERVER_PATH)
@app.route('/%s/device.xml' % SERVER_PATH)
def index():
	logger.debug(request.headers)
	return device()


@app.route('/%s/<request_file>' % SERVER_PATH)
def bridge(request_file):
	#print('Got request for %s from %s' % (request_file, request.environ.get('REMOTE_ADDR')))
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

	#return html epg guide based off of plex live
	elif request_file.lower().startswith('guide'):
		#try:
		epgguide()
		return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'guide.html')
		#except:
		#    return send_from_directory(os.path.join(os.path.dirname(sys.argv[0]), 'cache'), 'empty.png')

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
			playlist = build_playlist()
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
	else:
		logger.info("Unknown requested %r by %s", request_file, request.environ.get('REMOTE_ADDR'))
		abort(404, "Unknown request")


@app.route('/%s/auto/<request_file>' % SERVER_PATH)
#returns a piped stream, used for TVH/Plex Live TV
def auto(request_file):
	channel = request_file.replace("v","")
	logger.info("Channel %s playlist was requested by %s", channel,
			request.environ.get('REMOTE_ADDR'))
	sanitized_channel = ("0%d" % int(channel)) if int(channel) < 10 else channel
	sanitized_qual = 1 if int(channel) > 60 else QUAL
	template = "http://{0}.smoothstreams.tv:9100/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}"
	url =  template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	try:
		urllib.request.urlopen(url, timeout=2).getcode()
	except timeout:
		#special arg for tricking tvh into saving every channel first time
		sanitized_channel = '01'
		sanitized_qual = '3'
		url =  template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	except:
		sanitized_channel = '01'
		sanitized_qual = '3'
		url =  template.format(SRVR, SITE, sanitized_channel,sanitized_qual, token['hash'])
	runf = "%s -i %s -codec copy -loglevel error -f mpegts - " % (FFMPEGLOC, url)
	import subprocess

	def generate():
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
		#print(cmdline)
		FNULL = open(os.devnull, 'w')
		proc= subprocess.Popen( cmdline, stdout=subprocess.PIPE, stderr=FNULL )
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
		playlist = build_playlist()
		kodiplaylist = build_kodi_playlist()
		tvhplaylist = build_tvh_playlist()
		#Download icons, runs in sep thread, takes ~1min
		threading.Thread(target=dl_icons, args=(len(chan_map),)).start()
	except:
		logger.exception("Exception while building initial playlist: ")
		exit(1)

	try:
		thread.start_new_thread(thread_playlist, ())
	except:
		_thread.start_new_thread(thread_playlist, ())

	print("\n#######################################################")
	print("m3u8 url is %s/playlist.m3u8" %  urljoin(SERVER_HOST, SERVER_PATH))
	print("kodi m3u8 url is %s/kodi.m3u8" %  urljoin(SERVER_HOST, SERVER_PATH))
	print("EPG url is %s/epg.xml" % urljoin(SERVER_HOST, SERVER_PATH))
	print("Plex Live TV url is %s" % urljoin(SERVER_HOST, SERVER_PATH))
	print("TVHeadend network url is %s/tvh.m3u8" % urljoin(SERVER_HOST, SERVER_PATH))
	print("#######################################################\n")
	logger.info("Listening on %s:%d at %s/", LISTEN_IP, LISTEN_PORT, urljoin(SERVER_HOST, SERVER_PATH))
	#debug causes it to load twice on initial startup and every time the script is saved, TODO disbale later
	app.run(host=LISTEN_IP, port=LISTEN_PORT, threaded=True, debug=False)
	logger.info("Finished!")
