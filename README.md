##### requirements
* python3
* virtualenv

#### Begin by installing dependencies
```bash
make
sudo make install
sudo make run
```

######Start the API
```bash
source .venv/bin/activate
cd src/
python3 api.py
```
#### Run Daemons
##### To send out SMS messages
POST: localhost:6868/messages
```JSON
{
  "text" : "",
  "phonenumber" : ""
}
```
##### To read received SMS messages
GET: localhost:6868/messages
```bash
{
}
```
