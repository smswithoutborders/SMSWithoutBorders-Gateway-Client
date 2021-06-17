#!/bin/bash

if [ "$2" == "-cleanse" ] ; then
	for index in $(seq 0 $3)
	do
		mmcli -m $1 --messaging-delete-sms=$index
	done
fi
