#!/usr/bin/env python3

import os
import logging
import configparser
from telegram.ext import Updater, CommandHandler, CallbackContext

from node import Node
from deku import Deku
from mmcli_python.modem import Modem

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# class DekuControlBot(Node):
''' 
- should be able to inform of events
'''
class DekuControlBot(Deku):
    @classmethod
    def __init__(cls, token, configfile):
        cls.configfile = configfile

        cls.configs = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        cls.configs.read(cls.configfile)

        cls.updater = Updater(token=token, use_context=True)
        cls.dispatcher = cls.updater.dispatcher

        ''' handlers '''
        cls.start_handler = CommandHandler('start', cls.start)
        cls.status_handler = CommandHandler('status', cls.status)

        ''' bind handlers to dispatchers '''
        cls.dispatcher.add_handler(cls.start_handler)
        cls.dispatcher.add_handler(cls.status_handler)

    @classmethod
    def start(cls, update, context):
        ''' get the chat id and store in configs, will be used to continue message '''
        chat_id = update.effective_chat.id
        with open(cls.configfile, 'w') as w_configfile: #careful, if error here, the whole file is lost
            cls.configs['TELEGRAM']['CHAT_ID'] = str(chat_id)
            cls.configs.write(w_configfile)
            # self.logger('log file written....')
        cls.send_message(chat_id, f'Ready - {chat_id}', context)


    @classmethod
    def status(cls, update, context):
        status=Deku.status()
        message='Oops, no modems...'
        if len(status) > 0:
            message=''.join(status)
        cls.send_message(update.effective_chat.id, message, context)

    """
    @classmethod
    def send_message(cls, update, context, text):
        # logging.info(f'chat id: {update.effective_chat.id}')
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    """

    @classmethod
    def send_message(cls, chat_id, text, context=None):
        # logging.info(f'chat id: {update.effective_chat.id}')
        if context == None:
            context=CallBackContext
        context.bot.send_message(chat_id=chat_id, text=text)

    @classmethod
    def start_polling(cls):
        cls.updater.start_polling()

if __name__ == "__main__":
    configfile=os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
    configs = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    configs.read(configfile)

    token=configs['TELEGRAM']['TOKEN']
    DekuControlBot(token=token, configfile=configfile).start_polling()
