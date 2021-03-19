#!/bin/bash


$url=
d_command=$1
phonenumber=$2

if [ "$d_command" == "--send" ] ; then
	echo "Sending..."
	curl -X POST -H "Content-Type: application/json" -d '{"text":"$(date)","phonenumber":"${phonenumber}"}' $url
elif [ "$d_command" == "--send-bulk" ] ; then
	# File required to send this commmand
	# curl -X POST -H "Content-Type: application/json" -d '{"text":"$(date)","phonenumber":"${phonenumber}"}' $url
