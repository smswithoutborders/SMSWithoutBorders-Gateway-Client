### <a name="cluster_outgoing_sms"></a> Cluster - Outgoing SMS messages
[insert full description of Clusters and how they work]

##### node
[insert description]
##### server
[insert description]


#### Installation
```bash
pip3 install virtualenv
git clone https://github.com/smswithoutborders/Deku.git
cd Deku
make
make install
```
#### Configuration
<p>
Your clusters require a server to communicate with, and you will need to point to this in your configuration files.</p>

- Edit `.config/config.ini` ref:[link to example config file](.configs/example.config.ini)
```ini
[NODE]
api_id=<insert your server username here (same as an Afkanerd developer Auth ID)
api_key=<insert your server password here (same as an Afkanerd develper Auth Key)
```

##### configure events
There are 2 types of events (FAILED, SUCCESS). For each event, an array of ACTIONS can be listed. \
Each event can be configured to trigger an event when certain values are met. \
**Important** Event rules are not ISP specific and would be triggered regardless of modem's ISP \

- Edit `.config/events/rules.ini` ref:[link to example rules](.configs/events/example.rules.ini)

##### configure transmissions for events
Transmissions provide a means of externally receiving the states/results of triggered events. \
The means of transmission can be customized to third-party platforms you prefer e.g Telegram (default). \
\
To automatically enable transmissions, provide the required authentication details for whichever platforms you intend to use as a means for transmission.
- Edit `.config/extensions/platforms/telegram.ini` ref:[link Telegram config file](.configs/extensions/platforms/example.telegram.ini) \
All other supported platforms are placed in `.configs/extensions/platforms/

#### Running
##### Linux
```bash
. ~/.virtualenvs/deku/bin/activate
src/node.py
```
<b>To view all running logs</b>
```bash
tail -f src/service_files/logs/logs_nodes.txt
```



<h3>Setting up on Raspberry pi (tested on 4B)</h3>
<h4>Ubuntu Server</h4>
> https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
> https://itsfoss.com/connect-wifi-terminal-ubuntu/
