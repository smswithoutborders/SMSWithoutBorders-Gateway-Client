#!/bin/python

import mysql.connector

DATABASE = "deku"
TABLE = "sms"

def create_database(mysqlcursor, name :str ):
    mycursor.execute(f"CREATE DATABASE {name}")

def create_table( mysqlcursor, DATABASE, TABLE):
    statement = f"\
    CREATE TABLE {TABLE} (\
        id INT NOT NULL AUTO_INCREMENT,\
        other_id INT NULL,\
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

mydb = mysql.connector.connect( host = "localhost", user = "root", password = "asshole")
mycursor = mydb.cursor()
mycursor.execute("SHOW DATABASES")

databases = []
for database in mycursor:
    databases.append(list(database)[0])

print(">> Checking Databases....")
if DATABASE in databases:
    print("\t>> Database found")
else:
    print("\t>> Database not found")
    # Do something about it
    try:
        create_database( mycursor, DATABASE)
        print("\t[+] Database created!")
    except Exception as error:
        print( error )


mydb = mysql.connector.connect( host = "localhost", user = "root", password = "asshole", database=DATABASE)
mycursor = mydb.cursor()
mycursor.execute("SHOW TABLES")
tables = []
for table in mycursor:
    tables.append(list(table)[0])

print(">> Checking Tables...")
if TABLE in tables:
    print("\t>> Table found...")
else:
    print("\t>> Table not found...")
    # Do something about it
    try: 
        create_table( mycursor, DATABASE, TABLE)
        print("\t[+] Table created!")
    except Exception as error:
        print( error )

