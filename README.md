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

- Edit (.config/config.ini [.config](example.config.ini))
```ini
[NODE]
api_id=<insert your server username here (same as an Afkanerd developer Auth ID)
api_key=<insert your server password here (same as an Afkanerd develper Auth Key)
```

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
