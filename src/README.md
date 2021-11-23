### <a name="cluster_outgoing_sms"></a> Installation and Configuration
[insert full description of Clusters and how they work]

##### node
[insert description]
##### server
[insert description]


### Installation
#### Installing required Dependencies
- Erlang (minimum 23)
##### Arch
```bash
sudo pacman -S erlang
```

##### Ubuntu 20.04
```bash
sudo apt install wget
wget -O- https://packages.erlang-solutions.com/ubuntu/erlang_solutions.asc | sudo apt-key add -
echo "deb https://packages.erlang-solutions.com/ubuntu focal contrib" | sudo tee /etc/apt/sources.list.d/erlang-solution.list
sudo apt update
sudo apt-get install -y erlang-base \
                        erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                        erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                        erlang-runtime-tools erlang-snmp erlang-ssl \
                        erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl

```

#### Build and install
```bash
pip3 install virtualenv
git clone https://github.com/smswithoutborders/SMSWithoutBorders-Gateway-Client.git
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
make start
```
- To auto start on bootup
```bash
make enable
```

<b>To view all running logs</b>
```bash
tail -f src/services/logs/service.log
```

<h3>Setting up on Raspberry pi (tested on 4B)</h3>
<h4>Ubuntu Server</h4>
> https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
> https://itsfoss.com/connect-wifi-terminal-ubuntu/
