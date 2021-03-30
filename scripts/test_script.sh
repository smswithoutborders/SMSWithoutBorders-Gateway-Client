#!/bin/bash


url="http://127.0.0.1:6868"
d_command=$1
phonenumber=$2

if [ "$d_command" == "--send" ] ; then
	if [ "$phonenumber" == "" ] ; then
		echo "Phone number required but not provided.."
	else
		echo ">> Sending..."
		# date=$(date)
		curl -X POST -H "Content-Type: application/json" -d "{\"text\":\"$(date)\",\"phonenumber\":\"${phonenumber}\"}" "${url}/messages"
	fi

elif [ "$d_command" == "--received" ] ; then
	echo ">> Fetching received..."
	curl -X GET "${url}/messages"

elif [ "$d_command" == "--state" ] ; then
	echo ">> Checking state..."
	curl -X GET "${url}/state"

elif [ "$d_command" == "--logs" ] ; then
	echo ">> Fetching logs..."
	curl -X GET "${url}/logs"
fi
