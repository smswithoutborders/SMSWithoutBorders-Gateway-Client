#### Requirements
* python3
* pip3
* MySQL (mariadb)
* ModemManager (default on linux systems)

#### Installation
```bash
make
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
```bash
{
}
```
