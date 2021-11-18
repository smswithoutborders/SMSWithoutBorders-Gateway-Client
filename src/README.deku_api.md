# Deku API

#### Endpoints

##### Send SMS
> Protocol: POST
> Url: /modem/\<modem_index>/sms
> Body Type: JSON
> Body Content - 
```json
{
	"text":<string>, \
	"number":<string>, \
}
```
*Example*
```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"text":"Hello world", "number":"0000000"}' localhost:5000/modem/0/sms
```
