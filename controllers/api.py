#!/bin/python


import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)

if __name__ == "__main__":
    CONFIGS.read("config.ini")
    from ..modules.messagestore import MessageStore
else:
    CONFIGS.read("controllers/config.ini")
    from modules.messagestore import MessageStore


from flask import Flask, request, jsonify
app = Flask(__name__)

messageStore = MessageStore()
# messageStore = MessageStore(config=CONFIGS)

# Get current state of the daemon [idle, busy, help]
@app.route('/state')
def daemon_state():
    return "development"

@app.route('/messages', methods=['POST'])
def new_messages():
    request_body = request.json
    if not 'text' in request_body:
        return jsonify({"status":400, "message":"missing text"})

    if not 'number' in request_body:
        return jsonify({"status":400, "message":"missing number"})

    text = request_body["text"]
    number = request_body["number"]
    
    # TODO: put logger in here to log everything
    print(f"[+] New message...\n\t-text: {text}\n\t-number: {number}")

    tstate = MessageStore.insert({"text":text, "number":number})
    return jsonify({"status": 200, "tstate":tstate})

if CONFIGS["API"]["DEBUG"] == "1":
    # Allows server reload once code changes
    app.debug = True

app.run(host=CONFIGS["API"]["HOST"], port=CONFIGS["API"]["PORT"], debug=app.debug )
