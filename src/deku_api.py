#!/usr/bin/env python3

from flask import Flask, request, jsonify
from deku import Deku

import os
import traceback

from common.CustomConfigParser.customconfigparser import CustomConfigParser
from common.mmcli_python.modem import Modem

app = Flask(__name__)

def modem_sms_state():
    pass

@app.route('/modem/<modem_index>/sms', methods=['POST'])
def modem_send_sms(modem_index):
    data = None
    try:
        data = request.json
    except Exception as error:
        app.logger.exception(error)
        return 400

    if not 'text' in data:
        return 'misformed, text missing', 400
    if not 'number' in data:
        return 'misformed, number missing', 400

    text = data['text']
    number = data['number']

    try:
        deku.send(text=text, number=number, modem_index=modem_index)
        return 'sms sent', 200
    except subprocess.CalledProcessError as error:
        return "Failed to send", 408
    except Exception as error:
        return f"Error from system {error.message}", 500
    
    return 'failed to send sms', 400

@app.route('/modem/<modem_index>/sms', methods=['GET'])
def modem_read_sms(modem_index):
    try:
        messages = Modem(modem_index).SMS.list('received')

        lst_sms = []
        for msg_index in messages:
            sms=Modem.SMS(index=msg_index)

            lst_sms.append({
                "text":sms.text, 
                "number":sms.number,
                "timestamp":sms.timestamp })

        return jsonify(lst_sms), 200

    except Exception as error:
        app.logger.exception(error)
        return f"some error occured", 500

    return "read sms", 400

@app.route('/modem/<modem_index>/sms/<sms_index>', methods=['DELETE'])
def modem_delete_sms(modem_index, sms_index):
    return "delete sms", 200


if __name__ == "__main__":
    global deku

    try:
        configreader=CustomConfigParser(os.path.join(os.path.dirname(__file__), '..', ''))
        config=configreader.read(".configs/config.ini")
        config_isp_default = configreader.read('.configs/isp/default.ini')
        config_isp_operators = configreader.read('.configs/isp/operators.ini')

    except Exception as error:
        app.logger.critical(traceback.format_exc())

    else:
        deku = Deku(config, config_isp_default, config_isp_operators)

        app.run(debug=True)
