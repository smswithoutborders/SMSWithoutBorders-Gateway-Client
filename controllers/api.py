#!/bin/python


import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)
CONFIGS.read("config.ini")


from flask import Flask, request, jsonify
app = Flask(__name__)

# Get current state of the daemon [idle, busy, help]
@app.route('/state')
def daemon_state():
    return "development"

@app.route('/messages', methods=['POST'])
def new_messages():
    request_body = request.json
    return jsonify({"status": 200})

if CONFIGS["API"]["DEBUG"] == "1":
    # Allows server reload once code changes
    app.debug = True

app.run(host=CONFIGS["API"]["HOST"], port=CONFIGS["API"]["PORT"], debug=app.debug )
