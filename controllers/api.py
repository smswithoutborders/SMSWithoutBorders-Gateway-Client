#!/bin/python


import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)
CONFIGS.read("config.ini")


from flask import Flask
app = Flask(__name__)

# Get current state of the daemon [idle, busy, help]
@app.route('/state')
def daemon_state():
    return "development"

@app.route('/messages', methods=['POST'])
def new_messages():
    return True

if CONFIGS["DEBUG"] == "True":
    # Allows server reload once code changes
    app.debug = True

app.run(host=CONFIGS["HOST"], port=CONFIGS["PORT"], debug=app.debug )
