#!/bin/python

from models import read_daemon as sms_read
from models import send_daemon as sms_send

import start_routines
import configparser
import logging
import threading


format = "[%(asctime)s] >> %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
try:
    check_state = start_routines.sr_database_checks()
    if not check_state:
        logging.info("\t- Start routine check failed...")
except Exception as error:
    # print("Error raised:", error)
    print( error )
    exit()

else:
    send_thread = threading.Thread(target=sms_send.daemon, daemon=True)
    read_thread = threading.Thread(target=sms_read.daemon, daemon=True)

    send_thread.start()
    read_thread.start()

    send_thread.join()
    read_thread.join()
