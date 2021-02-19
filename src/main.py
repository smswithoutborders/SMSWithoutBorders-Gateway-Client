#!/bin/python


import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)

if __name__ == "__main__":
    CONFIGS.read("config.ini")
    from .. modules.messagestore import MessageStore
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
                number = row['number']
                tstate = MessageStore.insert({"text":text, "number":number})
                c_tstate.append( tstate )
        except Exception as err:
            print( err )

    return jsonify({"status":200, "c_tstate":c_tsate})

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

    return_json = {"status" :"", "tstate":""}
    try: 
        tstate = MessageStore.insert({"text":text, "number":number})
    except Exception as err:
        print( err )
    
    return jsonify(return_json)

if CONFIGS["API"]["DEBUG"] == "1":
    # Allows server reload once code changes
    app.debug = True

app.run(host=CONFIGS["API"]["HOST"], port=CONFIGS["API"]["PORT"], debug=app.debug )
