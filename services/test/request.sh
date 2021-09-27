#!/bin/bash


# Sending out messages
number=$1
curl -X POST http://localhost:15673/sms -H "Content-Type: application/json" -d '{"auth_id":"d86683a2d9c9baf792df29aed95c1e8c6981dcbc78c427e2c18ebd2cde3f2e33", "auth_key":"02fe2ca655842616fdf4f21549a01ece022c945d49665fb1b9fe35a164783d69", "data":[{"text":"Hello world", "number":"'$number'", "isp":"mtn"}]}'
