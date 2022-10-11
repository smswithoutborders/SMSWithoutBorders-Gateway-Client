"""
TODO
# Modem
    # Messages (incoming, outgoing)
    + create (send)
    + delete
    ---
    - date
    - text
    - number (incoming or receipient)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

import os
import logging
import time
import json
import configparser

from modem_manager import ModemManager
from message_store import MessageStore

logging.basicConfig(level='DEBUG')

app = Flask(__name__)

@app.route('/system/configs', methods=['GET'])
def fetch_configs():
    """
    """
    try:
        config_filepath = os.path.join(os.path.dirname(__file__), '../.configs', 'config.ini')
        configs = configparser.ConfigParser(interpolation=None)
        configs.read(config_filepath)

        configs_values = {}
        for sections in configs:
            if not sections in configs_values:
                configs_values[sections] = {}

            for key, value in configs[sections].items():
                configs_values[sections][key] = value

        return jsonify(configs_values), 200
    
    except Exception as error:
        logging.exception(error)
        return '', 500

@app.route('/system/configs/sections/<section_name>', methods=['POST'])
def update_configs(section_name: str):
    """
    """
    try:
        data = json.loads(request.data, strict=False)
    except Exception as error:
        logging.exception(error)
        return 'bad json', 400

    else:
        try:
            config_filepath = os.path.join(os.path.dirname(__file__), '../.configs', 'config.ini')
            configs = configparser.ConfigParser(interpolation=None)
            configs.read(config_filepath)

            if not section_name in configs:
                return 'invalid section name', 400

            else:
                for key, _value in data.items():
                    configs[section_name][key] = _value

                with open(config_filepath, 'w') as configfile:
                    configs.write(configfile)

                    return '', 200

                return 'error writing config file', 500
        
        except Exception as error:
            logging.exception(error)
            return '', 500


@app.route('/system/state', methods=['GET'])
def get_service_state():
    """
    """
    try:
        inbound_status = 'active' if os.system('systemctl is-active --quiet swob_inbound.service') == 0 else 'inactive'
        outbound_status = 'active' if os.system('systemctl is-active --quiet swob_outbound.service') == 0 else 'inactive'

        return jsonify({
            "inbound":inbound_status,
            "outbound":outbound_status})

    except Exception as error:
        logging.exception(error)
        return '', 500

    return jsonify(modems), 200

@app.route('/modems', methods=['GET'])
def api_get_modems():
    """
    """
    modems = []
    try:
        modems = get_modems()
    except Exception as error:
        logging.exception(error)
        return '', 500

    return jsonify(modems), 200

@app.route('/modems/<index>/sms', methods=['POST'])
def api_send_sms(index):
    """
    """
    index = index.replace(".", "/")
    try:
        data = json.loads(request.data, strict=False)
        text = data['text']
        number = data['number']

    except Exception as error:
        logging.exception(error)
        return 'bad json', 400

    else:
        try:
            send_sms(index, text, number)
        except Exception as error:
            logging.exception(error)
            return '', 500

    return "", 200

@app.route('/modems/<index>/sms', methods=['GET'])
def api_fetch_incoming_sms(index):
    """
    """
    index = index.replace(".", "/")
    messages = []
    try:
        messages = get_messages(index, 'incoming')
    except Exception as error:
        logging.exception(error)
        return '', 500

    return jsonify(messages), 200

@app.route('/modems/<index>/sms/<message_id>', methods=['DELETE'])
def api_delete_sms(index, message_id):
    """
    """
    index = index.replace(".", "/")
    try:
        row_count = delete_sms(message_id)
    except Exception as error:
        logging.exception(error)
        return '', 500

    return '', 200

def send_sms(modem_path, text, number) -> None:
    """
    """
    try:
        logging.info("Sending new sms message...")

        modem = modem_manager.get_modem(modem_path)

        timestamp = time.time()

        message_id = MessageStore().store(
                modem.get_sim().get_property("Imsi"), text, number, 
                timestamp, 'outgoing', 'sending')

        modem.messaging.send_sms(
                text=text,
                number=number)

    except Exception as error:
        logging.exception(error)

        try: 
            MessageStore().update(message_id, "status", "failed")

        except Exception as error:
            logging.exception(error)
            raise error

        raise error

    else:
        MessageStore().update(message_id, "status", "sent")
        logging.info("sent sms successfully!")


def delete_sms(message_id) -> int:
    """
    """
    try:
        row_count = MessageStore().delete(message_id)
    except Exception as error:
        raise error
    
    return row_count


def get_messages(modem_path, fetch_type=None) -> []:
    """
    Cannot talk directly with the modem because messages get removed from the 
    modem's message stack. 
    
    Talks with message_store sqlite storage for incoming messages.
    """
    modem = modem_manager.get_modem(modem_path)
    messages = []
    try:
        stored_messages = MessageStore().load(
                sim_imsi=modem.get_sim()
                .get_property("Imsi"), 

                _type=fetch_type)
    except Exception as error:
        raise error

    else:
        for message in stored_messages:
            ret_message = {}
            ret_message['id'] = message[0]
            ret_message['text'] = message[2]
            ret_message['number'] = message[3]
            ret_message['timestamp'] = message[4]
            ret_message['date_stored'] = message[5]
            ret_message['type'] = message[6]

            messages.append(ret_message)

    return messages

def get_modems() -> list:
    """
    """
    list_modems = modem_manager.list_modems()

    modems = []
    for modem_path, modem in list_modems.items():
        ret_modem = {}
        ret_modem["index"] = str(modem_path).replace("/", ".")
        ret_modem["imei"] = str(modem.get_3gpp_property("Imei"))
        ret_modem["operator_code"] = str(modem.get_3gpp_property("OperatorCode"))
        ret_modem["operator_name"] = str(modem.get_3gpp_property("OperatorName"))

        modems.append(ret_modem)

    return modems

def run(mm: ModemManager) -> None:
    """
    """
    global modem_manager
    modem_manager = mm

    host = "localhost"
    port = "12123"
    debug = True

    app.run(host=host, port=port, debug=debug, threaded=True )
