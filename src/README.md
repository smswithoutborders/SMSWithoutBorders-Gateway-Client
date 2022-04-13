## <a name="cluster_outgoing_sms"></a> Installation and Configuration

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
```
```bash
wget -O- https://packages.erlang-solutions.com/ubuntu/erlang_solutions.asc | sudo apt-key add -
```
```bash
echo "deb https://packages.erlang-solutions.com/ubuntu focal contrib" | sudo tee /etc/apt/sources.list.d/erlang-solution.list
```
```bash
sudo apt update
```
```bash
sudo apt-get install -y erlang-base \
                        erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                        erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                        erlang-runtime-tools erlang-snmp erlang-ssl \
                        erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl

```

#### Build and install

<p>Clone the repository</p>

```bash
git clone https://github.com/smswithoutborders/SMSWithoutBorders-Gateway-Client.git
```
```bash
cd SMSWithoutBorders-Gateway-Client
```

<p>Create your config files</p>

```bash
make
```

<p>Install more dependencies</p>

```bash
make install
```

#### Configuration
<p>
Your clusters require a server to communicate with, and you will need to point to this in your configuration files.</p>

- Edit `.configs/config.ini` ref:[link to example config file](.configs/example.config.ini)

- Follow [these steps](https://smswithoutborders.github.io/docs/developers/getting-started) in order to get your Auth ID and Auth key

```ini
[OPENAPI]
API_ID=<insert your server username here (same as an Afkanerd developer Auth ID)>
API_KEY=<insert your server password here (same as an Afkanerd develper Auth Key)>
```

##### configure events
There are 2 types of events (FAILED, SUCCESS). For each event, an array of ACTIONS can be listed. \
Each event can be configured to trigger an event when certain values are met. \
**Important** Event rules are not ISP specific and would be triggered regardless of modem's ISP \

- Edit `.configs/events/rules.ini` ref:[link to example rules](.configs/events/example.rules.ini)

##### configure transmissions for events
Transmissions provide a means of externally receiving the states/results of triggered events. \
The means of transmission can be customized to third-party platforms you prefer e.g Telegram (default). \
\
To automatically enable transmissions, provide the required authentication details for whichever platforms you intend to use as a means for transmission.
- Edit `.configs/extensions/platforms/telegram.ini` ref:[link Telegram config file](.configs/extensions/platforms/example.telegram.ini) \
All other supported platforms are placed in `.configs/extensions/platforms/

#### Running as system service
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

#### Running manually
##### Linux
- To run the outgoing (send out SMS messages)
    - Plug in your USB modem
    - Activate your virtual environment
    ```bash
    source venv/bin/activate
    ```
    - And:
    ```bash
    python3 src/main.py --log=DEBUG --module=outbound
    ```
- To run the incoming (receive and process incoming messages)
```bash
python3 src/main.py --log=DEBUG --module=inbound
```

<b>To view all running logs</b>
```bash
tail -f src/services/logs/service.log
```

### Setting up on Raspberry pi (tested on 4B)
#### Ubuntu Server
_Refs_
> https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
> https://itsfoss.com/connect-wifi-terminal-ubuntu/
