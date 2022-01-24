#!/usr/bin/env python3


import os
import logging
import configparser
import traceback
from telegram import KeyboardButton,ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot, ParseMode
import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler,Filters

class TelegramTransmissionLayer:
    # def __init__(self, token, configfile, adminfile=None):
    def __init__(self):
        self.configs=None
        self.configfile = ".configs/extensions/platforms/telegram.ini"

        self.configreader=CustomConfigParser(os.path.join(os.path.dirname(__file__), '..', ''))
        try:
            self.configs = self.configreader.read(self.configfile)
            # self.configs = self.configreader.read(self.authorizefile)
        except CustomConfigParser.NoDefaultFile as error:
            raise(error)
        except CustomConfigParser.ConfigFileNotFound as error:
            ''' with this implementation, it stops at the first exception - intended?? '''
            raise(error)
        except CustomConfigParser.ConfigFileNotInList as error:
            raise(error)

        self.configs = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.configs.read(self.configfile)

        try:
            self.token = self.configs['TELEGRAM']['token']
            self.bot = Bot(self.token)

        except telegram.error.InvalidToken as error:
            # raise(error)
            raise Exception("Telegram token not set")

        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher

        ''' handlers '''
        self.start_handler = CommandHandler('start', self.start)
        self.status_handler = CommandHandler('status', self.status)
        self.unknown_handler = MessageHandler(Filters.all, self.unknown)

        ''' bind handlers to dispatchers '''
        self.dispatcher.add_handler(self.start_handler)
        self.dispatcher.add_handler(self.status_handler)
        self.dispatcher.add_handler(self.unknown_handler)


        ''' constants '''
        self.bot_name = "Deku_ControlBot"
        self.request_phonenumber_text = "Hi there\nShare phone number below to continue..."



    def start(self, update, context):
        logging.info("start requested....")
        chat_id = update.effective_chat.id
        reply_request_phonenumber = KeyboardButton(text="Share phone number", request_contact=True)
        reply_request_phonenumber = ReplyKeyboardMarkup([[reply_request_phonenumber]])
        request_phonenumber = context.bot.send_message(chat_id, text=self.request_phonenumber_text, reply_markup=reply_request_phonenumber) 
        # context.bot.register_next_step_handler(message =request_phonenumber, callback=self.request_phonenumber) 

    def unknown(self, update, context):
        ''' in case commands come which have not been pre-programmed yet '''
        if 'message' in update.to_dict():
            message = update['message'].to_dict()
            if 'reply_to_message' in message:
                reply_to_message=message['reply_to_message']
                # print(f"Reply:", reply_to_message)
                _from=reply_to_message['from']

                ''' Checking = User Validation '''
                if 'username' in _from and 'is_bot' in _from:
                    if _from['username'] == self.bot_name and _from['is_bot'] and 'contact' in message:
                        # print(message['contact']['phone_number'])

                        ''' should be stored for some for of authentication '''
                        # print(message)
                        phonenumber = message['contact']['phone_number']
                        # print(">> phonenumber:", phonenumber)
                        
                        try:
                            if self.new_record(phonenumber, update.effective_chat.id):
                                context.bot.send_message(update.effective_chat.id, f"Great! Got number - {phonenumber}", 
                                        reply_markup=ReplyKeyboardRemove())
                        except Exception as error:
                            print(traceback.format_exc())

            """
            else:
                context.bot.send_message(update.effective_chat.id, f"Sorry, I do not understand that!")
            """

    def new_record(self, phonenumber, chat_id):
        log = f"Logging both phonenumber and chat ID {phonenumber} {chat_id}"
        logging.info(log)


        ''' checks if number is in the whitelist, then stores it, else dumps it '''
        if phonenumber[0] != '+':
            phonenumber = '+' + phonenumber

        if phonenumber in self.configs['WHITELIST']:
            with open(self.configfile, 'w') as fd_admin_list:
                self.configs['WHITELIST'][phonenumber] = str(chat_id)
                self.configs.write(fd_admin_list)

            return True
        else:
            logging.warning("phonenumber not found in whitelist")
        return False


    def status(cls, update, context):
        status=Deku.status()
        message='Oops, no modems...'
        if len(status) > 0:
            message=''.join(status)
        DekuControlBot.send_message(update.effective_chat.id, message, context)

    def send(self, text):
        ''' read every whitelist chat id '''
        list_chat_ids = self.configs['WHITELIST']
        for phonenumber, chat_id in list_chat_ids.items():
            print(f"* sending text to: {phonenumber}")
            if chat_id is not None or chat_id != '':
                self.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                print("\t* unregisterd contact")

    @staticmethod
    def send_message(token, chat_id, text, context=None):
        # logging.info(f'chat id: {update.effective_chat.id}')
        bot = Bot(token)
        bot.send_message(chat_id=chat_id, text=text)

    def start_polling(self):
        self.updater.start_polling()

if __name__ == "__main__":
    import sys

    logging.basicConfig(
            format='%(asctime)s|[%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            encoding='utf-8',
            level=logging.DEBUG)

    # configfile = '.configs/extensions/config.ini'
    configfile = '.configs/extensions/platforms/telegram.ini'
    configreader = CustomConfigParser()
    configs = configreader.read(configfile)
    token=configs['TELEGRAM']['TOKEN']

    if len(sys.argv) > 1:
        ''' this can be made better as a cli '''
        text = sys.argv[1]

        admin = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        admin.read(configfile)

        try:
            telegram_layer = TelegramTransmissionLayer()
            telegram_layer.send(text)
        except Exception as error:
            print( traceback.format_exc())
    else:
        telegram_layer = TelegramTransmissionLayer()
        telegram_layer.start_polling()
