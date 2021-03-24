#!/bin/python

import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)

CONFIGS.read("config.ini")
from ldatastore import Datastore
from libs.lmodems import Modems

from flask import Flask, request, jsonify
app = Flask(__name__)

# datastore.get_datastore()
# datastore = Datastore(config=CONFIGS)

# Get current state of the daemon [idle, busy, help]
@app.route('/state')
def daemon_state():
    return "development"

@app.route('/messages', methods=['POST', 'GET'])
def new_messages():
    if request.method == 'POST':
        request_body = request.json
        if not 'text' in request_body:
            return jsonify({"status":400, "message":"missing text"})

        if not 'phonenumber' in request_body:
            return jsonify({"status":400, "message":"missing phonenumber"})

        text = request_body["text"]
        phonenumber = request_body["phonenumber"]
        
        # TODO: put logger in here to log everything
        print(f"[+] New message...\n\t-text: {text}\n\t-phonenumber: {phonenumber}")

        return_json = {"status" :"", "tstate":""}
        try: 
            # TODO: Determine ISP before sending messages
            datastore = Datastore(configs_filepath="libs/config.ini")
            messageID = datastore.new_message(text=text, phonenumber=phonenumber, isp="MTN", _type="sending")
            return_json["status"] = 200
            return_json["messageID"] = messageID
        except Exception as err:
            print( f"[err]: {err}" )
    

    elif request.method == 'GET':
        print("[?] Fetching messages....")
        return_json = {"status" :"", "tstate":""}
        try:
            datastore = Datastore(configs_filepath="libs/config.ini")
            messages = datastore.get_all_received_messages()
            return_json["status"] = 200
            return_json["messages"] = messages
        except Exception as err:
            print( f"[err]: {err}" )


    return jsonify(return_json)

if CONFIGS["API"]["DEBUG"] == "1":
    # Allows server reload once code changes
    app.debug = True

app.run(host=CONFIGS["API"]["HOST"], port=CONFIGS["API"]["PORT"], debug=app.debug )
