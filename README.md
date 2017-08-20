sstvProxy
========

A small flask app to proxy SSTV streams to Plex Media Server (DVR).

#### sstvProxy configuration
1. In sstvProxy.py configure options as per your setup.
2. Create a virtual enviroment: ```$ virtualenv venv```
3. Activate the virtual enviroment: ```$ . venv/bin/activate```
4. Install the requirements: ```$ pip install -r requirements.txt```
5. Finally run the app with: ```$ python sstvProxy.py```

#### systemd service configuration
A startup script for Ubuntu can be found in sstvProxy.service (change paths in sstvProxy.service to your setup), install with:

    $ sudo cp sstvProxy.service /etc/systemd/system/sstvProxy.service
    $ sudo systemctl daemon-reload
    $ sudo systemctl enable sstvProxy.service
    $ sudo systemctl start sstvProxy.service

#### Plex configuration
Enter the IP of the host running sstvProxy including port 5004, eg.: ```192.168.1.50:5004```
