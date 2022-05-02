# Deku API

#### Running API
To have Deku API running (assuming entire project has been cloned already)
```bash
git submodule update --init --recursive
. venv/bin/activate
python3 -m venv venv
pip3 install -r requirements.txt
python3 src/deku_api.py
```

#### Endpoints

##### Fetch state of cluster
> Protocol: GET \
> Url: /system/state \
> Returns: -
```python
active or inactive, 200
```
```bash
failed 4xx
error 5xx
```
*Example*
```bash
curl localhost:5000/system/state
```

##### Fetch modems
> Protocol: GET \
> Url: /modems \
> Returns: -
```json
[
	{... modem information ...}
], 200
```
```bash
failed 4xx
error 5xx
```
*Example*
```bash
curl localhost:5000/modems
```

##### Send SMS
> Protocol: POST \
> Url: /modems/\<modem_index>/sms \
> Body Type: JSON \
> Body Content - 
```json
{"text":"", "number":""}
```
> Returns: -
```curl
success 200
failed 4xx
error 5xx
```
*Example*
```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"text":"Hello world", "number":"0000000"}' localhost:5000/modems/0/sms
```

##### Fetch received SMS
> Protocol: GET \
> Url: /modems/\<modem_index>/sms \
> Returns: -
```json
[
	{"text":"", "number":"", "timestamp":"", "index":""}
], 200
```
```bash
failed 4xx
error 5xx
```
*Example*
```bash
curl localhost:5000/modems/0/sms
```

##### Delete SMS
> Protocol: DELETE \
> Url: /modems/\<modem_index>/sms/\<sms_index> \
> Returns: -
```curl
success 200
failed 4xx
error 5xx
```
*Example*
```bash
curl -X DELETE localhost:5000/modems/0/sms
```
