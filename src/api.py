#!/bin/python

import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)

CONFIGS.read("config.ini")
from ldatastore import Datastore

from flask import Flask, request, jsonify
app = Flask(__name__)

datastore = Datastore(configs_filepath="libs/config.ini")
# datastore.get_datastore()
# datastore = Datastore(config=CONFIGS)

# Get current state of the daemon [idle, busy, help]
@app.route('/state')
def daemon_state():
    return "development"

@app.route('/messages/bulk', methods=['POST'])
def new_bulk_message():
    request_body = request.json
    
    if not 'file' in request_body:
        return jsonify({"status":400, "message":"missing file"})

    c_tstate = []
    with open(filename) as bulkfile:
        csv_reader = csv.DictReader( bulkfile )
        try: 
            for row in csv_reader:
                text = row['text']
                number = row['phonenumber']
                tstate = Datastore.insert({"text":text, "phonenumber":number})
                c_tstate.append( tstate )
        except Exception as err:
            print( err )

    return jsonify({"status":200, "c_tstate":c_tsate})

@app.route('/messages', methods=['POST'])
def new_messages():
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
        messageID = datastore.new_message(text=text, phonenumber=phonenumber, isp="MTN")
        return_json["status"] = 200
        return_json["messageID"] = messageID
    except Exception as err:
        print( f"[err]: {err}" )
    
    return jsonify(return_json)

if CONFIGS["API"]["DEBUG"] == "1":
    # Allows server reload once code changes
    app.debug = True

app.run(host=CONFIGS["API"]["HOST"], port=CONFIGS["API"]["PORT"], debug=app.debug )
