# Gateway Client Incoming Module
- Gateway clients receive and [process](processing) incoming SMS messages.
- Every USB modem connected to them acts as an independent [Node](nodes) capable of receiving and processing SMS messages.
- Gateway clients are utilized by SMSWithoutBorders android app to receive and [forward](forwarding) incoming messages online/offline servers.
- USB modems connected to Gateway clients identify themselves by [publishing](publishing) their [MSISDN]() after a duration to a Gateway server.
- Nodes attain their phone numbers by sending a [MSISDN request SMS message](MSISDN_request_sms_message) to [seeder Gateway clients](seeder_gateway_clients). 

<a name="processing" />

### Processing

<a name="forwarding" />

#### Forwarding

<a name="MSISDN_request_sms_message" />

#### MSISDN request SMS message
By default Nodes do not know their own MSISDN (but can have their [IMSI]()). MSISDN are required for [Gateway Server's broadcasting](gateway_server_broadcast) to app users and publishing on the [Available Gateway Clients dashboard](). \
\
Nodes acquire their MSISDN by sending an SMS to a [seeder gateway](seeder_gateway_MSISDN) which contains their IMSI. Once the request are completed the IMSI and MSISDN of the Node are stored on the server and are [queried]() anytime the Gateway server requires that information.

<a name="modules" />

### Modules

<a name="Modes" />

### Modes

<a name="seeder_gateway_clients" />

#### Seeder Gateway Clients
