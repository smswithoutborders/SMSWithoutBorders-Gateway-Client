#!/bin/python

import os
import configparser
import threading
import subprocess
import traceback

from subprocess import Popen, PIPE
from flask import Flask, request, jsonify
from flask_cors import CORS

from datastore import Datastore
import deduce_isp as isp
import daemon

app = Flask(__name__)
CORS(app)

# datastore.get_datastore()
# datastore = Datastore(config=CONFIGS)

# Get current state of the daemon [idle, busy, help]
CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
    exit()


@app.route('/state')
def daemon_state():
    systemd_output=None
    try: 
       systemd_output = subprocess.check_output(["systemctl", "is-active", "deku.service"], stderr=subprocess.STDOUT).decode('utf-8').replace('\n', '')
    except subprocess.CalledProcessError as error:
        print(traceback.format_exc())
        systemd_output=error.output.decode('utf-8').replace('\n', '')
        pass
    return jsonify({"status": 200, "state": systemd_output})


@app.route('/logs')
def get_logs():
    return_json = {"status" :""}
    try: 
        # TODO: Determine ISP before sending messages
        # datastore = Datastore(configs_filepath="libs/configs/config.ini")
        datastore = Datastore()
        logs = datastore.get_logs()
        return_json["status"] = 200
        return_json["logs"] = logs
        return_json["size"] = len(logs)
    except Exception as err:
        print(traceback.format_exc())

    return jsonify(return_json)

@app.route('/messages', methods=['POST', 'GET'])
def new_messages():
    if request.method == 'POST':
        request_body = request.json
        if not 'text' in request_body:
            return jsonify({"status":400, "message":"missing text"})

        if not 'phonenumber' in request_body:
            return jsonify({"status":400, "message":"missing phonenumber"})

        text = request_body["text"]
        phonenumber = isp.rm_country_code(request_body["phonenumber"])
        dec_isp=isp.deduce_isp(phonenumber)

        # TODO: authenticate min length
        # TODO: put logger in here to log everything
        print(f"[+] New sending message...\n\t-text: {text}\n\t-phonenumber: {phonenumber},\n\t-isp: {dec_isp}")

        return_json = {"status" :""}
        try: 
            # TODO: Determine ISP before sending messages
            # datastore = Datastore(configs_filepath="libs/configs/config.ini")
            datastore = Datastore()
            messageID = datastore.new_message(text=text, phonenumber=phonenumber, isp=dec_isp, _type="sending")
            return_json["status"] = 200
            return_json["messageID"] = messageID
        except Exception as err:
            print(traceback.format_exc())
    

    elif request.method == 'GET':
        print("[?] Fetching messages....")
        return_json = {"status" :"", "tstate":""}
        try:
            # datastore = Datastore(configs_filepath="libs/configs/config.ini")
            datastore = Datastore()
            messages = datastore.get_all_received_messages()
            return_json["status"] = 200
            return_json["messages"] = messages
            return_json["size"] = len(messages)
        except Exception as err:
            print(traceback.format_exc())


    return jsonify(return_json)

if CONFIGS["API"]["DEBUG"] == "1":
    # Allows server reload once code changes
    pass
    # app.debug = True

tDaemon = threading.Thread(name="master daemon", target=daemon.start, daemon=True)
tDaemon.start()

app.run(host=CONFIGS["API"]["HOST"], port=CONFIGS["API"]["PORT"], debug=app.debug )
tDaemon.join()
