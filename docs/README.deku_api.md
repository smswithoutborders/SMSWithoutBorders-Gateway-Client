# Deku API

#### Endpoints

##### Update configs
> Protocol: POST \
> Url: /system/configs/sections/<section_name> \
> Body Type: JSON \
> Body Content - 
```json
{
	"[key]":"value"
}
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
-d '{"FRIENDLY_NAME":"Afkanerd"}' localhost:5000/system/configs/sections/OPENAPI
```

##### Fetch configs
> Protocol: GET \
> Url: /system/configs \
> Returns: -
```json
{
	"[section]": {
		"[key]": "value"
	}
}
```
```bash
failed 4xx
error 5xx
```
*Example*
```bash
curl localhost:5000/system/configs
```

##### Restart state of cluster
> Protocol: POST \
> Url: /system/state/restart \
> Returns: -
```bash
success 200
failed 4xx
error 5xx
```
*Example*
```bash
curl -X POST localhost:5000/system/state/restart
```

##### Fetch state of cluster
> Protocol: GET \
> Url: /system/state \
> Returns: -
```json
{
	"inbound":"active|inactive",
	"outbound":"active|inactive"
}
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
