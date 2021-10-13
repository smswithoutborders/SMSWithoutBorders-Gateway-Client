#!/usr/bin/env python3

import os
import logging
import configparser
from telegram.ext import Updater, CommandHandler

from node import Node
from deku import Deku

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# class DekuControlBot(Node):
class DekuControlBot:
    @classmethod
    def __init__(cls, token):
        cls.updater = Updater(token=token, use_context=True)
        cls.dispatcher = cls.updater.dispatcher

        ''' handlers '''
        cls.start_handler = CommandHandler('status', cls.status)

        ''' bind handlers to dispatchers '''
        cls.dispatcher.add_handler(cls.start_handler)

    @classmethod
    def status(cls, update, context):
        indexes=Deku.modems_ready()

        if len(indexes) < 1:
            cls.send_message(update, context, 'Oops, no modems...')

        else:
            for index in indexes:
                modem=Deku.Modem(index)
                message=f'\
                imei={modem.imei}\n\
                state={modem.state}\n\
                model={modem.modem}\n\
                dbus_path={modem.dbus_path}\n\
                power_state={modem.power_state}\n\
                operator_code={modem.operator_code}\n\
                operator_name={modem.operator_name}'

                cls.send_message(update, context, message)

    @classmethod
    def send_message(cls, update, context, text):
        # logging.info(f'chat id: {update.effective_chat.id}')
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    @classmethod
    def start_polling(cls):
        cls.updater.start_polling()

if __name__ == "__main__":
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))

    token=config['TELEGRAM']['TOKEN']
    DekuControlBot(token).start_polling()
