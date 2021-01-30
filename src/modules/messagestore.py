#!/bin/python

import mysql.connector
from datetime import date

class MessageStore:
    def __init__(self, configs=None, configs_filepath=None):
        import configparser
        self.CONFIGS = configparser.ConfigParser(interpolation=None)

        if configs != None and __name__ == "__main__":
            self.CONFIGS = configs

        elif configs_filepath != None:
            self.CONFIGS.read( configs_filepath )

        else:
            print(">> Defaulting to . config.ini")
            self.CONFIGS.read( "config.ini" )

        HOST = self.CONFIGS["MYSQL"]["HOST"]
        USER = self.CONFIGS["MYSQL"]["USER"]
        PASSWORD = self.CONFIGS["MYSQL"]["PASSWORD"]
        DATABASE = self.CONFIGS["MYSQL"]["DATABASE"]

        self.mysqlDBConnector = mysql.connector.connect( host=HOST, user=USER, password=PASSWORD, database=DATABASE)
        self.mysqlDBcursor = mydb.cursor()

    def insert( self, data :dict):
        query = f"INSERT INTO {tb_messages} SET text=\"{data['text']}\", phonenumber=\"{data['phonenumber']}\""

        try:
            self.mysqlDBcursor.execute( query )
            insert_id = self.mysqlDBConnector.commit()
        except mysql.connector.Error as err:
            raise Exception( err )
        else:
            return {"insert_id":insert_id, "value": True}
