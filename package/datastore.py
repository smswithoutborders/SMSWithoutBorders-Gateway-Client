#!/bin/python import mysql.connector
import os
import pymysql
import mysql.connector
from datetime import date

# rewrite message store to allow for using as a class extension
class Datastore(object):
    def __init__(self):
        import configparser
        self.CONFIGS = configparser.ConfigParser(interpolation=None)
        PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.mysql.ini')
        if os.path.exists( PATH_CONFIG_FILE ):
            self.CONFIGS.read(PATH_CONFIG_FILE)
        else:
            raise Exception(f"config file not found: {PATH_CONFIG_FILE}")

        self.HOST = self.CONFIGS["MYSQL"]["HOST"]
        self.USER = self.CONFIGS["MYSQL"]["USER"]
        self.PASSWORD = self.CONFIGS["MYSQL"]["PASSWORD"]
        # self.DATABASE = self.CONFIGS["MYSQL"]["DATABASE"]
        self.DATABASE = "deku"

        self.conn = pymysql.connect( host=self.HOST, user=self.USER, password=self.PASSWORD, database=self.DATABASE, cursorclass=pymysql.cursors.SSDictCursor)
        # self.cursor = self.conn.cursor(buffered=True)
        self.cursor = self.conn.cursor()

    def new_log(self, messageID):
        query=f"INSERT INTO logs SET messageID={messageID}"
        try:
            self.cursor.execute( query )
            self.conn.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return self.cursor.lastrowid

    def update_log(self, messageLogID:int, status:str, message:str):
        query=f"UPDATE logs SET status='{status}', message=%s WHERE id={messageLogID}"
        try:
            self.cursor.execute( query, [message])
            self.conn.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            self.cursor.lastrowid

    def release_message(self, messageID:int, status:str=None):
        if status is not None:
            query=f"UPDATE messages SET status='{status}' WHERE id={messageID}"
        else:
            query=f"UPDATE messages SET claimed_modem_imei=NULL WHERE id={messageID}"
        try:
            self.cursor.execute( query )
            self.conn.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            self.cursor.lastrowid

    def release_pending_messages(self, claimed_modem_imei):
        query=f"UPDATE logs, messages SET logs.status='invalid', claimed_modem_imei=NULL where logs.status='pending' and (messages.id=logs.messageID and messages.claimed_modem_imei=%s)"
        try:
            self.cursor.execute( query, [claimed_modem_imei] )
            self.conn.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            self.cursor.lastrowid

    def claim_message(self, messageID:int, modem_imei:str):
        query=f"UPDATE messages SET claimed_modem_imei={modem_imei} WHERE id={messageID}"
        try:
            self.cursor.execute( query )
            self.conn.commit()

        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            self.cursor.lastrowid

    def acquire_message(self, modem_index:int, modem_imei:str, isp:str, router:bool=False):
        '''
            TODO: 
                - Filter by last come first out
        '''

        query=""
        query_vars = []
        if router:
            query = f"SELECT * FROM messages where claimed_modem_imei is NULL and (type='sending' or type='routing') and status='pending' LIMIT 1"

        else:
            query = f"SELECT * FROM messages where claimed_modem_imei is NULL and type='sending' and isp=%s and status='pending' LIMIT 1"
            query_vars = [isp]

        # print("[+] Claim query: ", query)
        try:
            self.cursor.execute( query, query_vars)
            sms_message = self.cursor.fetchall()
            # print(sms_message, type(sms_message), len(sms_message))
            counter = 0
            mn_sms_message = None
            for row in sms_message:
                messageID = row["id"]
                # print(row["text"], messageID)
                self.claim_message(messageID, modem_imei)
                
                if counter < 1:
                    mn_sms_message = row
                    ++counter

            return mn_sms_message

        except mysql.connector.Error as err:
            raise Exception( err )


    def new_message(self, text:str, phonenumber:str, isp:str, _type:str, claimed_modem_imei=None):
        query = f"INSERT INTO messages SET text=%s, phonenumber=%s, isp=%s, type=%s"
        query_vars = [text, phonenumber, isp, _type]
        if not claimed_modem_imei==None:
            query += f", claimed_modem_imei=%s"
            query_vars.append( claimed_modem_imei )
        try:
            self.cursor.execute( query, query_vars )
            self.conn.commit()
            messageID = self.cursor.lastrowid
            # messageID = self.conn.commit()
        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return messageID

    def get_all_received_messages(self):
        query = "SELECT * FROM messages WHERE type='received'"
        try:
            self.cursor.execute( query )
            messages = self.cursor.fetchall()
            return messages
        except mysql.connector.Error as err:
            raise Exception( err )

    def get_deku_configs(self):
        query = f"SELECT * FROM configs LIMIT 1"
        try:
            self.cursor.execute( query )
            configs = self.cursor.fetchall()
            return configs
        except mysql.connector.Error as err:
            raise Exception( err )

    def get_logs(self):
        query=f"SELECT * FROM logs"
        try:
            self.cursor.execute( query )
            configs = self.cursor.fetchall()
            return configs
        except mysql.connector.Error as err:
            raise Exception( err )
