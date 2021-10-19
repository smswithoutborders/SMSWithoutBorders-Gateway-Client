#!/usr/bin/env python3


"""
Usage: this is customized for each user as a template
- If you want a telegram remote control for your clusters, create one
- then use this template for remote manipulation

- This should be hosted along side deku for best experience
- If failure to communicate, can mean Deku is currently offline
"""


"""
#### TODO
- Bot should be able to manage individual nodes (specified by users)
"""

import os
import logging
import configparser
import traceback
from telegram import KeyboardButton,ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler,Filters

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
    def __init__(cls, token, configfile, adminfile=None):
        cls.token = token
        cls.configfile = configfile
        cls.adminfile = adminfile

        cls.configs = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        cls.configs.read(cls.configfile)

        cls.admins = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        cls.admins.read(cls.adminfile)

        cls.updater = Updater(token=token, use_context=True)
        cls.dispatcher = cls.updater.dispatcher

        ''' handlers '''
        cls.start_handler = CommandHandler('start', cls.start)
        cls.status_handler = CommandHandler('status', cls.status)
        cls.unknown_handler = MessageHandler(Filters.all, cls.unknown)

        ''' bind handlers to dispatchers '''
        cls.dispatcher.add_handler(cls.start_handler)
        cls.dispatcher.add_handler(cls.status_handler)
        cls.dispatcher.add_handler(cls.unknown_handler)


        ''' constants '''
        cls.bot_name = "Deku_ControlBot"
        cls.request_phonenumber_text = "Hi there\nShare phone number below to continue..."

    @classmethod
    def start(cls, update, context):
        # print(context)
        # print(update)
        ''' get the chat id and store in configs, will be used to continue message '''
        logging.info("start requested....")
        chat_id = update.effective_chat.id
        with open(cls.configfile, 'w') as w_configfile: #careful, if error here, the whole file is lost
            cls.configs['TELEGRAM']['CHAT_ID'] = str(chat_id)
            cls.configs.write(w_configfile)
            # self.logging('log file written....')
        # cls.send_message(chat_id, f'Ready - {chat_id}', context)
        reply_request_phonenumber = KeyboardButton(text="Share phone number", request_contact=True)
        reply_request_phonenumber = ReplyKeyboardMarkup([[reply_request_phonenumber]])
        request_phonenumber = context.bot.send_message(chat_id, text=cls.request_phonenumber_text, reply_markup=reply_request_phonenumber) 
        # context.bot.register_next_step_handler(message =request_phonenumber, callback=cls.request_phonenumber) 

    @classmethod
    def unknown(cls, update, context):
        ''' in case commands come which have not been pre-programmed yet '''
        if 'message' in update.to_dict():
            message = update['message'].to_dict()
            if 'reply_to_message' in message:
                reply_to_message=message['reply_to_message']
                # print(f"Reply:", reply_to_message)
                _from=reply_to_message['from']

                ''' Checking = User Validation '''
                if 'username' in _from and 'is_bot' in _from:
                    if _from['username'] == cls.bot_name and _from['is_bot'] and 'contact' in message:
                        # print(message['contact']['phone_number'])

                        ''' should be stored for some for of authentication '''
                        # print(message)
                        phonenumber = message['contact']['phone_number']
                        # print(">> phonenumber:", phonenumber)
                        
                        try:
                            if cls.new_record(phonenumber, update.effective_chat.id):
                                context.bot.send_message(update.effective_chat.id, f"Great! Got number - {phonenumber}", 
                                        reply_markup=ReplyKeyboardRemove())
                        except Exception as error:
                            print(traceback.format_exc())

            """
            else:
                context.bot.send_message(update.effective_chat.id, f"Sorry, I do not understand that!")
            """


    @classmethod
    def new_record(cls, phonenumber, chat_id):
        log = f"Logging both phonenumber and chat ID {phonenumber} {chat_id}"
        logging.info(log)


        ''' checks if number is in the whitelist, then stores it, else dumps it '''
        if phonenumber[0] != '+':
            phonenumber = '+' + phonenumber

        if phonenumber in cls.admins['WHITELIST']:
            with open(cls.adminfile, 'w') as fd_admin_list:
                cls.admins['WHITELIST'][phonenumber] = str(chat_id)
                cls.admins.write(fd_admin_list)

            return True
        else:
            logging.warning("phonenumber not found in whitelist")
        return False


    @classmethod
    def status(cls, update, context):
        status=Deku.status()
        message='Oops, no modems...'
        if len(status) > 0:
            message=''.join(status)
        DekuControlBot.send_message(update.effective_chat.id, message, context)

    """
    @classmethod
    def send_message(cls, update, context, text):
        # logging.info(f'chat id: {update.effective_chat.id}')
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    """

    @staticmethod
    def send_message(token, chat_id, text, context=None):
        # logging.info(f'chat id: {update.effective_chat.id}')
        bot = Bot(token)
        bot.send_message(chat_id=chat_id, text=text)

    @classmethod
    def start_polling(cls):
        cls.updater.start_polling()

if __name__ == "__main__":
    import sys
    configfile=os.path.join(os.path.dirname(__file__), 'extensions', 'config.ini')
    adminfile=os.path.join(os.path.dirname(__file__), 'extensions', 'admins.ini')

    configs = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    configs.read(configfile)
    token=configs['TELEGRAM']['TOKEN']

    if len(sys.argv) > 1:
        ''' this can be made better as a cli '''
        number=sys.argv[1]
        text = sys.argv[2]

        admin = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        admin.read(adminfile)

        DekuControlBot(token=token, configfile=configfile, adminfile=adminfile).send_message(token, chat_id=admin['WHITELIST'][number], text=text)
    else:
        DekuControlBot(token=token, configfile=configfile, adminfile=adminfile).start_polling()
