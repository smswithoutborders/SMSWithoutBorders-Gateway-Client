#!/bin/python

import subprocess
from modules._sms_ import SMS 
from modules.modem import Modem 
from modules.modems import Modems 
from modules import start_routines

# Beginning daemon from here
modems = Modems()

# check to make sure everything is set for takefoff
print(">> Starting system diagnosis...")
try:
    check_state = start_routines.sr_database_checks()
    if not check_state:
        print("\t- Start routine check failed...")
except Exception as error:
    # print("Error raised:", error)
    print( error )
else:
    print("\t- All checks passed.... proceeding...")
    try:
        modems.listen_for_modems()
    except Exception as error:
        print( error)
