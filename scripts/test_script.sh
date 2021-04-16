#!/bin/bash


url="http://127.0.0.1:6868"
d_command=$1
protocol=$2

gmail_templated_message="gmail:send:Afkanerd progressing on SMSwithoutborders:$2:Hi Nerds,\nThis is a test message! If you are reading this, it means it was successful!\nBest Works\n-Wisdom @sw\\0b"

if [ "$d_command" == "--send" ] ; then
	if [ "$protocol" == "" ] ; then
		echo "Phone number required but not provided.."
	else
		echo ">> Sending..."
		# date=$(date)
		curl -X POST -H "Content-Type: application/json" -d "{\"text\":\"$(date)\",\"phonenumber\":\"${protocol}\"}" "${url}/messages"
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

elif [ "$d_command" == "--route" ] ; then
	echo ">> Routing..."
	mysql -u root -p -e "INSERT INTO deku.messages SET text='$gmail_templated_message',phonenumber='$2',type='routing'"
fi
