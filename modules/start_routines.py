#!/bin/python

import mysql.connector
from datetime import date

DATABASE = "deku"
TABLE = "sms"
mydb = None
mysqlcursor = None

def create_database(mysqlcursor, name :str ):
    mysqlcursor.execute(f"CREATE DATABASE {name}")

def create_table( mysqlcursor, DATABASE, TABLE):
    statement = f"\
        CREATE TABLE {TABLE} (\
            id INT NOT NULL AUTO_INCREMENT,\
            other_id INT NULL,\
            state ENUM('pending','sent','invalid') NOT NULL DEFAULT 'pending',\
            text TEXT NOT NULL,\
            phonenumber VARCHAR(24) NOT NULL,\
            source_id INT NULL,\
            date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\
            mdate TIMESTAMP on update CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\
            PRIMARY KEY(id),\
            UNIQUE(other_id)\
        )"
    try:
        mysqlcursor.execute( statement )
    except mysql.connector.Error as err:
        raise Exception( err )

# CHECK DATABASE
def sr_database_checks():
    global mysqlcursor, mydb
    mydb = mysql.connector.connect( host = "localhost", user = "root", password = "asshole")
    mysqlcursor = mydb.cursor()
    mysqlcursor.execute("SHOW DATABASES")

    databases = []
    for database in mysqlcursor:
        databases.append(list(database)[0])

    print(">> Checking Databases....")
    if DATABASE in databases:
        print("\t>> Database found")
    else:
        print("\t>> Database not found")
        # Do something about it
        try:
            create_database( mysqlcursor, DATABASE)
            print("\t[+] Database created!")
        except Exception as error:
            print( error )


    # CHECK TABLES
    mydb = mysql.connector.connect( host = "localhost", user = "root", password = "asshole", database=DATABASE)
    # TODO: Check if connected
    mysqlcursor = mydb.cursor()
    mysqlcursor.execute("SHOW TABLES")
    tables = []
    for table in mysqlcursor:
        tables.append(list(table)[0])

    print(">> Checking Tables...")
    if TABLE in tables:
        print("\t>> Table found...")
    else:
        print("\t>> Table not found...")
        # Do something about it
        try: 
            create_table( mysqlcursor, DATABASE, TABLE)
            print("\t[+] Table created!")
        except Exception as error:
            print( error )

    return {"value": True}

def insert_sms( data :dict):
    global mysqlcursor, mydb
    statement = f"INSERT INTO {data['table']} SET text=\"{data['text']}\", phonenumber=\"{data['phonenumber']}\""
    # statement = f"INSERT INTO {data['table']}(text, phonenumber) values (%s, %s)"
    data = (data["text"], data["phonenumber"])

    try:
        # insert_id = mysqlcursor.execute( statement, data )
        mysqlcursor.execute( statement )
        insert_id = mydb.commit()
    except mysql.connector.Error as err:
        raise Exception( err )
    else:
        # if insert_id == None, there's an issue
        return {"insert_id":insert_id, "value": True}


if __name__ == "__main__":
    try:
        sr_check_state = sr_database_checks()
        if sr_check_state["value"]:
            print( ">> Start check passed - Inserting test values")
            text = f"[DEKU|TEST_SMS]: {date.today()}"
            phonenumber = "000000000"
            try:
                insert_state = insert_sms({"table":TABLE, "text":text, "phonenumber":phonenumber})
                print("\t[+] Insert successful")
                print(f"\t>> Insert log: {insert_state}")
            except Exception as error:
                print( error )
    except Exception as error:
        print(error)
