#!/usr/bin/env python3

import os
import logging
import configparser
from telegram.ext import Updater, CommandHandler

from deku import Deku

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class DekuControlBot(Deku):
    @classmethod
    def __init__(cls):
        cls.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        cls.config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))

        token=cls.config['TELEGRAM']['TOKEN']
        cls.updater = Updater(token=token, use_context=True)
        cls.dispatcher = cls.updater.dispatcher

        ''' handlers '''
        cls.start_handler = CommandHandler('status', cls.status)

        ''' bind handlers to dispatchers '''
        cls.dispatcher.add_handler(cls.start_handler)

    @classmethod
    def status(cls, update, context):
        logging.info('* status called')
        cls.send_message(update, context, 'status...')

    @classmethod
    def send_message(cls, update, context, text):
        # logging.info(f'chat id: {update.effective_chat.id}')
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    @classmethod
    def start_polling(cls):
        cls.updater.start_polling()

if __name__ == "__main__":
    DekuControlBot().start_polling()
