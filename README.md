sstvProxy
========

A small flask app to proxy SSTV streams to Plex Media Server (DVR).

Python version is always the most up to date, the executables in each of the folders are simply compiled versions of the python using pyinstaller, there will be no functional differences.

You only need one file as they're all identical. Create a folder somewhere put the file in and run it. Setup should be self-explanatory.

###Clients Supported:
Kodi(v17+ i suspect due to SSL)
VLC
iPlayTV
Perfect Player (not windows)
TVirl
TVHeadend
Plex Live TV/DVR
Quadstream

###Hosts tested:
Windows (7,10)
Linux (Ubuntu, Debian)
Mac (Sierra 10.12.3)
RPi (Rasbian using python)

#### sstvProxy venv usage
1. In sstvProxy.py configure options as per your setup.
2. Create a virtual enviroment: ```$ virtualenv venv```
3. Activate the virtual enviroment: ```$ . venv/bin/activate```
4. Install the requirements: ```$ pip3 install -r requirements.txt```
5. Finally run the app with: ```$ python3 sstvProxy.py```

#### systemd service configuration
A startup script for Ubuntu can be found in sstvProxy.service (change paths in sstvProxy.service to your setup), install with:

    $ sudo cp sstvProxy.service /etc/systemd/system/sstvProxy.service
    $ sudo systemctl daemon-reload
    $ sudo systemctl enable sstvProxy.service
    $ sudo systemctl start sstvProxy.service

#### Plex configuration
Refer: https://imgur.com/a/OZkN0

#### TVH Configuration
Refer: http://smoothstreams.tv/board/index.php?topic=1832.msg10698#msg10698


#### Advanced Settings

You can have as many or as few as you want and the file itself is optional. If you don't care for the option then don't even include it in the file, just delete it.

There now exists an advanced settings example file on git. If this is in the same folder as the proxy it will detect it on launch and parse any settings that are within. Currently the accepted settings are:

    Enable/disable network discovery - "networkdiscovery": 1 (1 or 0)
    Custom ffmpeg locations "ffmpegloc": "C:\\ffmpeg\\bin\\ffmpeg.exe" (note the double slashes)
    Custom kodi control username "kodiuser": "string"
    Custom kodi control password "kodipass": "string"

If you want to output a playlist that combines the SSTV channels with another playlist you already have then these options are for you:

    A url source for the above EXTM3URL = 'url/string'
    A group name for the above, in order to fileter between them in client EXTM3UNAME = 'string'
    A file source for the above, url has priority though EXTM3UFILE = 'path/string'

If you wish to use feed YAP into TVH and then TVH into Plex use the below:

    set true TVHREDIRECT = False
    TVH url you use TVHURL = '127.0.0.1'
    username TVHUSER = ''
    password TVHPASS = ''


#### Commandline Arguments

'install' - forces recreation of the install function which creates certain files, such as the tvh internal grabber
'headless' - uses command line for initial setup rather than gui
'tvh' - each call to a piped channel will return channel 01 which is a 24/7 channel so will always generate a positive result, this allows TVH to create all services
