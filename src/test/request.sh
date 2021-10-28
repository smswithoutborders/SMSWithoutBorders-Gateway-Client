#!/bin/bash


# Sending out messages
# this API is hosted from Deku, admin creds would be bonded on it once passed before authentication begins
number=$1
curl -X POST http://localhost:15673/sms -H "Content-Type: application/json" -d '{"auth_id":"d8fa1ea1b0bb44557ece9c9707ba2cad52ba570ee4f9847c6a836b955775df06", "auth_key":"10189606f77bdef8d9a0bd46ecdf9115c8d7e9f33eb5bbafb4cc985f70845da4", "project_id": "bbeffbe0-208c-11ec-8178-57945bdf329f", "data":[{"text":"Hello world", "number":"'$number'", "isp":"mtn"}]}'
