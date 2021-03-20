#!/bin/python

import mysql.connector
from datetime import date

DATABASE = "deku"
TABLE = "messages"
TABLE_LOG = "logs"
mydb = None
mysqlcursor = None

# A little bit too extensive
columns = {
        "id": "INT NOT NULL AUTO_INCREMENT",
        "other_id": "INT NULL",
        "state": "ENUM('pending','sent','claimed','invalid') NOT NULL DEFAULT 'pending'",
        "claimed_modem_imei": "VARCHAR(255) NULL",
        "claimed_time": "TIMESTAMP NULL",
        "text": "TEXT NOT NULL",
        "phonenumber": "VARCHAR(24) NOT NULL",
        "isp": "VARCHAR(255) NULL",
        "source_id": "INT NULL",
        "date": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "mdate": "TIMESTAMP on update CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
    }

columns_logs = {
        "id": "INT NOT NULL AUTO_INCREMENT",
        "messageID": "INT NULL",
        "status": "ENUM('pending','sent','claimed','invalid') NOT NULL DEFAULT 'pending'",
        "message": "TEXT NOT NULL",
        "date": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "mdate": "TIMESTAMP on update CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
    }

def create_database(mysqlcursor, name :str ):
    mysqlcursor.execute(f"CREATE DATABASE {name}")

def check_tables(DATABASE, TABLE, custom_columns):
    global mysqlcursor
    supplus = []
    minus = []
    try:
        mysqlcursor.execute(f"SHOW COLUMNS FROM {TABLE}")
        cols = mysqlcursor.fetchall()
        cols = [list(col)[0] for col in cols]
        value = True
        for col in cols:
            if col not in custom_columns.keys():
                supplus.append( col )
                value = False

        col_keys = list(custom_columns.keys())
        # print( cols )
        for col in col_keys:
            # print(f"{col} ---> {cols}")
            if col not in cols:
                print("[+] Appending minus...", custom_columns[col])
                minus.append( [col,custom_columns[col]] )
                value = False
    except mysql.connector.Error as err:
        raise Exception( err )
    return_value= {"value": value, "extra": supplus, "missing": minus}
    # print( return_value )
    return return_value

def create_table( mysqlcursor, DATABASE, TABLE):
    # TODO: Maybe add a value to account for test SMS messages
    statement = None
    for col in columns:
        if statement == None:
            statement = f"CREATE TABLE {TABLE} ("
        else:
            statement += ","
        statement += f"{col} {columns[col]}"
    statement += ",PRIMARY KEY(id), UNIQUE(other_id))"
    # print( statement )
    try:
        mysqlcursor.execute( statement )
    except mysql.connector.Error as err:
        raise Exception( err )

def alter_table( DATABASE, TABLE, alters ):
    global mysqlcursor
    for alter in alters:
        statement = f"ALTER TABLE {TABLE} ADD COLUMN {alter[0]} {alter[1]}"
        print(f"[+] Altering with: {statement}")
        try:
            mysqlcursor.execute( statement )
            mysqlcursor.commit( )
        except mysql.connector.Error as err:
            raise Exception( err )

def set_connection( host, user, password, database=None):
    global mysqlcursor, mydb
    mydb = mysql.connector.connect( host= host, user= user, password= password, database=database)
    mysqlcursor = mydb.cursor()

# CHECK DATABASE
def sr_database_checks():
    global mysqlcursor, mydb
    set_connection(host="localhost", user="root", password="asshole")
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
    set_connection(host = "localhost", user = "root", password = "asshole", database=DATABASE)
    # TODO: Check if connected
    mysqlcursor = mydb.cursor()
    mysqlcursor.execute("SHOW TABLES")
    tables = []
    for table in mysqlcursor:
        tables.append(list(table)[0])

    print(">> Checking Tables...")
    if TABLE in tables:
        print(f"\t>> Table found{TABLE}...")
        check_state = check_tables( DATABASE, TABLE, columns)
        # if not check_state["value"]:
        if not check_state["value"]:
            # Do something like repair or rebuild entire table
            print("\t>> Table does not match with requirements")
            print(f"\t>> {check_state}")
            try:
                alter_table( DATABASE, TABLE, check_state["missing"] )
                print("\t[+] Changes to table added!")
            except Exception as err:
                raise Exception( err)
    else:
        print(f"\t>> Table not found{TABLE}...")
        # Do something about it
        try: 
            create_table( mysqlcursor, DATABASE, TABLE)
            print("\t[+] Table created!")
        except Exception as error:
            raise Exception( error )

    if TABLE_LOG in tables:
        print(f"\t>> Table found: {TABLE_LOG}...")
        check_state = check_tables( DATABASE, TABLE_LOG, columns_logs)
        # if not check_state["value"]:
        if not check_state["value"]:
            # Do something like repair or rebuild entire table
            print("\t>> Table does not match with requirements")
            print(f"\t>> {check_state}")
            try:
                alter_table( DATABASE, TABLE_LOG, check_state["missing"] )
                print("\t[+] Changes to table added!")
            except Exception as err:
                raise Exception( err)
    else:
        print(f"\t>> Table not found: {TABLE_LOG}...")
        # Do something about it
        try: 
            create_table( mysqlcursor, DATABASE, TABLE_LOG)
            print("\t[+] Table created!")
        except Exception as error:
            raise Exception( error )

    mydb.close()
    return {"value": True}
