#!/bin/python

import mysql.connector
from datetime import date

class MessageStore:
    def __init__( config=None ):
        import configparser
        self.CONFIGS = configparser.ConfigParser(interpolation=None)

        if configs==None:
            self.CONFIGS.read("config.ini")
        else:
            self.CONFIGS = config

        HOST = CONFIGS["HOST"]
        USER = CONFIGS["USER"]
        PASSWORD = CONFIGS["PASSWORD"]
        DATABASE = CONFIGS["DATABASE"]

        self.mysqlDBConnector = mysql.connector.connect( host=HOST, user=USER, password=PASSWORD, database=DATABASE)
        self.mysqlDBcursor = mydb.cursor()

    def insert( data :dict):
        query = f"INSERT INTO {tb_messages} SET text=\"{data['text']}\", phonenumber=\"{data['phonenumber']}\""

        try:
            self.mysqlDBcursor.execute( query )
            insert_id = self.mysqlDBConnector.commit()
        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return {"insert_id":insert_id, "value": True}
