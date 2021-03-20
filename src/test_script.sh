#!/bin/bash


url="http://127.0.0.1:3000"
d_command=$1
phonenumber=$2

if [ "$phonenumber" == "" ] ; then
	echo "Phone number required but not provided.."

elif [ "$d_command" == "--send" ] ; then
	echo "Sending..."
	# date=$(date)
	curl -X POST -H "Content-Type: application/json" -d "{\"text\":\"$(date)\",\"phonenumber\":\"${phonenumber}\"}" "${url}/messages"
fi
