#### Requirements
* python3
* pip3
* MySQL (mariadb)
* ModemManager (default on linux systems)

#### Installation
```bash
make
# goto package/configs/configs.mysql.ini and configure your settings before proceeding
# goto package/configs/configs.ini and configure your settings before proceeding

sudo make install
sudo make run
```

### API Endpoints
#### Sending SMS
> POST: localhost:6868/messages
```JSON
{
	"text" : "",
	"phonenumber" : ""
}
```

#### Reading received SMS messages
> GET: localhost:6868/messages
```JSON
{
}
```

#### Checking state
> GET: localhost:6868/state
```JSON
{
	"status" : 200,
	"state" : "active" || "inactive"  
}
```
If `status != 200` : No Daemon has not been installed, and is not running manually<br>
If `status == 200` and `state == "inactive"`: Daemon has not been installed, but is running manually<br>
If `status == 200` and `state == "failed"`: Daemon successfully installed, but failed to start <br>
If `status == 200` and `state == "active"`: Daemon has been installed<br>

#### Acquiring logs
> GET: localhost:6868/logs
```JSON
{
      "date": "Thu, 01 Apr 2021 16:59:01 GMT", 
      "id": 116, 
      "mdate": "Thu, 01 Apr 2021 16:59:06 GMT", 
      "message": "successfully sent the SMS", 
      "messageID": 110, 
      "other_id": null, 
      "status": "sent"
    },....
```

<h2>Beta features</h2>
<h3>Setting up on Raspberry pi (tested on 4B)</h3>
<h4>Ubuntu Server</h4>
- https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#4-boot-ubuntu-server<br>
- https://itsfoss.com/connect-wifi-terminal-ubuntu/
