# Gateway Client Incoming Module
- Gateway clients receive and [process](processing) incoming SMS messages.
- Every USB modem connected to them acts as an independent [Node](nodes) capable of receiving and processing SMS messages.
- Gateway clients are utilized by SMSWithoutBorders android app to receive and [forward](forwarding) incoming messages online/offline servers.
- USB modems connected to Gateway clients identify themselves by [publishing](publishing) their [MSISDN]() after a duration to a Gateway server.
- Nodes attain their phone numbers by sending a [MSISDN request SMS message](MSISDN_request_sms_message) to [seeder Gateway clients](seeder_gateway_clients).
- Gateway clients send [ping]() messages after custom time periods to Gateway servers. This keeps the server from deleting the Gateway client.

<a name="processing" />

### Processing

<a name="forwarding" />

#### Forwarding

<a name="MSISDN_request_sms_message" />

#### Pinging

<a name="pinging" />


#### MSISDN request SMS message
By default Nodes do not know their own MSISDN (but can have their [IMSI]()). MSISDN are required for [Gateway Server's broadcasting](gateway_server_broadcast) to app users and publishing on the [Available Gateway Clients dashboard](). \
\
Nodes acquire their MSISDN by sending an SMS to a [seeder gateway](seeder_gateway_MSISDN) which contains their IMSI. Gateway Clients acquire seeder addresses by [querying a remote Gateway Server](). They will use hard-coded seeder addresses in cases where remote Gateway Servers are not accessible (usually Client cannot connect online). Seeders [respond]() to the Client with the received IMSI and MSISDN. IMSI and MSISDN are not stored on seeder gateways and any request for information from them requires the entire self introduction to proceed.

<a name="modules" />

### Modules

<a name="Modes" />

### Modes

<a name="seeder_gateway_clients" />

#### Seeder Gateway Clients
- Seeders have the following:
  1. Seeder functionality turned on in the conf file (seeder = True)
  2. MSISDN and SMS present per seeding node
  3. SMS capability
