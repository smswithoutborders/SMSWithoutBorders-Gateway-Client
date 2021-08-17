#### Requirements
* python3
* pip3
* MySQL (mariadb)
* ModemManager (default on linux systems)

#### Installation
```bash
git submodule update --init --recursive
make
# goto package/configs/configs.mysql.ini and configure your settings before proceeding
# goto package/configs/configs.ini and configure your settings before proceeding

sudo make install
sudo make run
```

#### Deku Usage
* Run --help for the options


<h2>Beta features</h2>
<h3>Setting up on Raspberry pi (tested on 4B)</h3>
<h4>Ubuntu Server</h4>
- https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
- https://itsfoss.com/connect-wifi-terminal-ubuntu/
