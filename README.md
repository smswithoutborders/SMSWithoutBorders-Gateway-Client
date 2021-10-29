### Cluster - Outgoing SMS messages
Everything is a file, everything can be configured. \
Everything is exaggerated to the extent it implies, but there is the option to configure aspects a user will most likely need to customize.
#### Installation
```bash
git clone https://github.com/smswithoutborders/Deku.git
cd Deku
make
```
#### Configuration
<p>
Your clusters require a server to communicate with, and you will need to point to this in your configuration files.</p>

- Edit `.config/config.ini` ref:[.config](example.config.ini)`
```ini
[NODE]
api_id=<insert your server username here (same as an Afkanerd developer Auth ID)
api_key=<insert your server password here (same as an Afkanerd develper Auth Key)
```

##### configure events
There are 2 types of events (FAILED, SUCCESS). For each event, an array of ACIONS can be listed. \
Each event can be configured to trigger an event when certain values are met. \
**Important** Event rules are not ISP specific and would be triggered regardless of modem's ISP\

- Edit `.config/events/rules.ini` ref:[.config/events](example.rules.ini)`

##### configure Deku
Commands for Deku can be automated. Using the `--label` flag you can trigger commands found in the label config file.
- Edit `.config/extensions/labels.ini` ref:[.config/extensions](example.labels.ini)

#### Running
##### Linux
```bash
. ~/.virtualenvs/deku/bin/activate
src/node.py
```



<h3>Setting up on Raspberry pi (tested on 4B)</h3>
<h4>Ubuntu Server</h4>
> https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
> https://itsfoss.com/connect-wifi-terminal-ubuntu/
