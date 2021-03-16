#!/bin/python

import mysql.connector
from datetime import date

class MessageStore:
    def __init__(self, config=None ):
        import configparser
        self.CONFIGS = configparser.ConfigParser(interpolation=None)

        if config==None:
            self.CONFIGS.read("config.ini")
        else:
            self.CONFIGS = config

        HOST = self.CONFIGS["MYSQL"]["HOST"]
        USER = self.CONFIGS["MYSQL"]["USER"]
        PASSWORD = self.CONFIGS["MYSQL"]["PASSWORD"]
        DATABASE = self.CONFIGS["MYSQL"]["DATABASE"]

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

    def fetch( sort_latest=True):
        query = f"SELECT * FROM {tb_messages} WHERE state='pending' ORDER BY date DESC LIMIT 1"

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

