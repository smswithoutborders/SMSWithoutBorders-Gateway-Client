## <a name="cluster_outgoing_sms"></a> Installation and Configuration

### Installation
#### Installing required Dependencies
- python3

#### Dependencies
##### Ubuntu
`sudo apt install build-essential libpython3-dev libdbus-1-dev`

`sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`

`sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev python3-venv`

##### Arch
`sudo pacman -S python-gobject gtk3`

`sudo pacman -S python cairo pkgconf gobject-introspection gtk3`

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

- Be sure to set your connection URL to point to the [RabbitMQ server](https://developers.smswithoutborders.com:15671).
```ini
CONNECTION_URL=developers.smswithoutborders.com
```

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
    - For outgoing OpenAPI messages:
    ```bash
    python3 src/main.py --log=DEBUG --module=outbound
    ```
    - To run the incoming (receive and process incoming messages)
    ```bash
    python3 src/main.py --log=DEBUG --module=inbound
    ```

<b>Logs - </b>

**systemd**

<small>Inbound</small>
```bash
journalctl -af -u swob_inbound.service
```

<small>Outbound</small>
```bash
journalctl -af -u swob_outbound.service
```

### Sending out SMS messages Using OpenAPI
With [OpenAPI](https://smswithoutborders-openapi.readthedocs.io/en/latest/overview.html), you can send out single and bulk SMS messages through the Gateway Client. After the gateway client as a system service or manually, you are good to start sending out SMS messages.


### Setting up on Raspberry pi (tested on 4B)
#### Ubuntu Server
_Refs_
> https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
> https://itsfoss.com/connect-wifi-terminal-ubuntu/
