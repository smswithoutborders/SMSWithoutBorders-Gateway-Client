# Deku API

#### Endpoints

##### Send SMS
> Protocol: POST \
> Url: /modem/\<modem_index>/sms \
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
-d '{"text":"Hello world", "number":"0000000"}' localhost:5000/modem/0/sms
```

##### Fetch received SMS
> Protocol: GET \
> Url: /modem/\<modem_index>/sms \
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
curl localhost:5000/modem/0/sms
```

##### Delete SMS
> Protocol: DELETE \
> Url: /modem/\<modem_index>/sms/\<sms_index> \
> Returns: -
```curl
success 200
failed 4xx
error 5xx
```
*Example*
```bash
curl -X DELETE localhost:5000/modem/0/sms
```
