import tkinter
import os,sys
from json import dump

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

class GUI(object):
	# def changeLabel(self):
	#     text = "You have entered " + self.someName.get()
	#     self.labelText.set(text)
	#     self.someName.delete(0, tkinter.END)
	#     self.someName.insert(0, "You've clicked!")

	def client_exit(self, config):
		global playlist, kodiplaylist, QUAL, USER, PASS, SRVR, SITE, STRM, KODIPORT, LISTEN_IP, LISTEN_PORT, EXTIP, EXT_HOST, SERVER_HOST
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'proxysettingstest.json'), 'w') as fp:
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
		EXT_HOST = "http://" + EXTIP + ":" + str(LISTEN_PORT)
		SERVER_HOST = "http://" + LISTEN_IP + ":" + str(LISTEN_PORT)
		app = GUI2()

	def __init__(self):
		app = tkinter.Tk()
		app.title("YAP Setup")
		app.geometry('600x450')

		self.labelText = tkinter.StringVar()
		self.labelText.set("Initial Setup")
		label1 = tkinter.Label(app, textvariable=self.labelText, height=2)
		label1.grid(row=1, column=2)

		self.noteText = tkinter.StringVar()
		self.noteText.set("Notes")
		noteText = tkinter.Label(app, textvariable=self.noteText, height=2)
		noteText.grid(row=1, column=3)


		self.labelUsername = tkinter.StringVar()
		self.labelUsername.set("Username")
		labelUsername = tkinter.Label(app, textvariable=self.labelUsername, height=2)
		labelUsername.grid(row=2, column=1)
		#
		userUsername = tkinter.StringVar()
		userUsername.set("blogs@hotmail.com")
		self.username = tkinter.Entry(app, textvariable=userUsername)
		self.username.grid(row=2, column=2)
		#
		self.noteUsername = tkinter.StringVar()
		self.noteUsername.set("mystreams will not be an email address")
		noteUsername = tkinter.Label(app, textvariable=self.noteUsername, height=2)
		noteUsername.grid(row=2, column=3)


		self.labelPassword = tkinter.StringVar()
		self.labelPassword.set("Password")
		labelPassword = tkinter.Label(app, textvariable=self.labelPassword, height=2)
		labelPassword.grid(row=3, column=1)
		#
		userPassword = tkinter.StringVar()
		userPassword.set("blogs123")
		self.password = tkinter.Entry(app, textvariable=userPassword)
		self.password.grid(row=3, column=2)


		self.labelServer = tkinter.StringVar()
		self.labelServer.set("Server")
		labelServer = tkinter.Label(app, textvariable=self.labelServer, height=2)
		labelServer.grid(row=4, column=1)

		userServer = tkinter.StringVar()
		userServer.set('East-NY')
		self.server = tkinter.OptionMenu(app, userServer, *[x[0] for x in serverList])
		self.server.grid(row=4, column=2)


		self.labelSite = tkinter.StringVar()
		self.labelSite.set("Site")
		labelSite = tkinter.Label(app, textvariable=self.labelSite, height=2)
		labelSite.grid(row=5, column=1)

		userSite = tkinter.StringVar()
		userSite.set('StreamTVnow')
		self.site = tkinter.OptionMenu(app, userSite, *[x[0] for x in providerList])
		self.site.grid(row=5, column=2)


		self.labelStream = tkinter.StringVar()
		self.labelStream.set("Stream Type")
		labelStream = tkinter.Label(app, textvariable=self.labelStream, height=2)
		labelStream.grid(row=6, column=1)

		userStream = tkinter.StringVar(app)
		userStream.set('HLS')
		self.stream = tkinter.OptionMenu(app,userStream,*[x.upper() for x in streamtype])
		self.stream.grid(row=6, column=2)


		self.labelQuality = tkinter.StringVar()
		self.labelQuality.set("Quality")
		labelQuality = tkinter.Label(app, textvariable=self.labelQuality, height=2)
		labelQuality.grid(row=7, column=1)

		userQuality = tkinter.StringVar()
		userQuality.set('HD')
		self.quality = tkinter.OptionMenu(app, userQuality, *[x[0] for x in qualityList])
		self.quality.grid(row=7, column=2)


		self.labelIP = tkinter.StringVar()
		self.labelIP.set("Listen IP")
		labelIP = tkinter.Label(app, textvariable=self.labelIP, height=2)
		labelIP.grid(row=8, column=1)

		userIP = tkinter.StringVar()
		userIP.set("127.0.0.1")
		self.ip = tkinter.Entry(app, textvariable=userIP)
		self.ip.grid(row=8, column=2)

		self.noteIP = tkinter.StringVar()
		self.noteIP.set("If using on other machines then set a static IP and use that.")
		noteIP = tkinter.Label(app, textvariable=self.noteIP, height=2)
		noteIP.grid(row=8, column=3)


		self.labelPort = tkinter.StringVar()
		self.labelPort.set("Listen Port")
		labelPort = tkinter.Label(app, textvariable=self.labelPort , height=2)
		labelPort.grid(row=9, column=1)

		userPort = tkinter.IntVar()
		userPort.set(80)
		self.port = tkinter.Entry(app, textvariable=userPort)
		self.port.grid(row=9, column=2)

		self.notePort = tkinter.StringVar()
		self.notePort.set("If 80 doesn't work try 99")
		notePort = tkinter.Label(app, textvariable=self.notePort, height=2)
		notePort.grid(row=9, column=3)


		self.labelKodiPort = tkinter.StringVar()
		self.labelKodiPort.set("KodiPort")
		labelKodiPort = tkinter.Label(app, textvariable=self.labelKodiPort, height=2)
		labelKodiPort.grid(row=10, column=1)

		userKodiPort = tkinter.IntVar(None)
		userKodiPort.set(8080)
		self.kodiport = tkinter.Entry(app, textvariable=userKodiPort)
		self.kodiport.grid(row=10, column=2)

		self.noteKodiPort = tkinter.StringVar()
		self.noteKodiPort.set("Only change if you've had to change the Kodi port")
		noteKodiPort = tkinter.Label(app, textvariable=self.noteKodiPort, height=2)
		noteKodiPort.grid(row=10, column=3)


		self.labelExternalIP = tkinter.StringVar()
		self.labelExternalIP.set("External IP")
		labelExternalIP = tkinter.Label(app, textvariable=self.labelExternalIP, height=2)
		labelExternalIP.grid(row=11, column=1)

		userExternalIP = tkinter.StringVar()
		userExternalIP.set("127.0.0.1")
		self.externalip = tkinter.Entry(app, textvariable=userExternalIP)
		self.externalip.grid(row=11, column=2)

		self.noteExternalIP = tkinter.StringVar()
		self.noteExternalIP.set("Enter your public IP or Dynamic DNS,\nfor use when you wish to use this remotely.")
		noteExternalIP = tkinter.Label(app, textvariable=self.noteExternalIP, height=2)
		noteExternalIP.grid(row=11, column=3)

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
			return config

		button1 = tkinter.Button(app, text="Submit", width=20,command=lambda: self.client_exit(gather()))
		button1.grid(row=12, column=2)

		app.mainloop()

class GUI2(object):
	# def changeLabel(self):
	#     text = "You have entered " + self.someName.get()
	#     self.labelText.set(text)
	#     self.someName.delete(0, tkinter.END)
	#     self.someName.insert(0, "You've clicked!")

	def client_exit(self, config):
		exit()

	def __init__(self):
		app = tkinter.Tk()
		app.title("YAP Setup")
		app.geometry('600x450')
		button1 = tkinter.Button(app, text="Submit", width=20,command=lambda: self.client_exit(gather()))
		button1.grid(row=12, column=2)

		app.mainloop()
GUI() #calling the class to run
