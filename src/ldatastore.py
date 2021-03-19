#!/bin/python import mysql.connector
import mysql.connector
from datetime import date

# rewrite message store to allow for using as a class extension
class Datastore(object):
    def __init__(self, config=None ):
        import configparser
        self.CONFIGS = configparser.ConfigParser(interpolation=None)

        if config==None:
            self.CONFIGS.read("libs/config.ini")
        else:
            self.CONFIGS = config

        self.HOST = self.CONFIGS["MYSQL"]["HOST"]
        self.USER = self.CONFIGS["MYSQL"]["USER"]
        self.PASSWORD = self.CONFIGS["MYSQL"]["PASSWORD"]
        self.DATABASE = self.CONFIGS["MYSQL"]["DATABASE"]

    def get_datastore(self):
        self.conn = mysql.connector.connect( host=self.HOST, user=self.USER, password=self.PASSWORD, database=self.DATABASE)
        self.cursor = self.conn.cursor(buffered=True)
        return self

    def new_log(self, messageID):
        query=f"INSERT INTO logs SET messageID={messageID}"
        try:
            self.cursor.execute( query )
            messageLogID = self.cursor.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return messageLogID

    def update_log(self, messageLogID:int, status:str, message:str):
        query=f"UPDATE logs SET status={status}, message={message} WHERE id={messageLogID}"
        try:
            self.cursor.execute( query )
            messageLogID = self.cursor.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return messageLogID

    def release_message(self, messageID:int):
        query=f"UPDATE messages SET claimed_modem_imei=NULL WHERE id={messageID}"
        try:
            self.cursor.execute( query )
            messageID = self.cursor.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return messageID

    def claim_message(self, messageID:int, modem_imei:str):
        query=f"UPDATE messages SET claimed_modem_imei={modem_imei} WHERE id={messageID}"
        try:
            self.cursor.execute( query )
            messageID = self.cursor.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return messageID

    def acquire_message(self, modem_index:int, modem_imei:str):
        '''
            TODO: 
                - Filter by last come first out
        '''

        query = f"SELECT * FROM messages where claimed_modem_imei is NULL LIMIT 1"
        try:
            sms_message = self.cursor.execute( query )
            if not sms_message==None:
                self.claim_message(sms_message.id, modem_imei)

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return sms_message


'''
    def insert( data :dict):
        query = f"INSERT INTO {tb_messages} SET text=\"{data['text']}\", phonenumber=\"{data['phonenumber']}\""

        try:
            self.mysqlDBcursor.execute( query )
            insert_id = self.mysqlDBConnector.commit()
        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return {"insert_id":insert_id, "value": True}


    def fetch_for( data :dict):
        query = f"SELECT * FROM {tb_messages} WHERE "
        for key, value in data:

            appended=False
            # if one key needs to or many values
            if type(value)==type({}):
                query += "("
                _appended=False
                for _key, _value in value:
                    if _appended:
                        query += "OR "
                    if type(_value)==type(0): #int
                        query += f"{key}={value} "
                    else:
                        query += f"{key}='{value}' "
                    _appended=True
                query += ") "
            if appended:
                query+= "AND "
            if type(_value)==type(0): #int
                query += f"{key}={value} "
            else:
                query += f"{key}='{value}' "
            appended=True

        query += "WHERE state='pending' ORDER BY date DESC LIMIT 1"
'''
