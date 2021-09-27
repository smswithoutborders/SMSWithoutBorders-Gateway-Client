#!/bin/bash


# Sending out messages
number=$1
curl -X POST http://localhost:15673/sms -H "Content-Type: application/json" -d '{"auth_id":"guest", "auth_key":"guest", "data":[{"text":"Hello world", "number":"'$number'", "isp":"mtn"}]}'
