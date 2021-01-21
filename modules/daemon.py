#!/bin/python

import subprocess
from _sms_ import SMS 
from modem import Modem 
from modems import Modems 
import start_routines

# Beginning daemon from here
modems = Modems()

# check to make sure everything is set for takefoff
print(">> Starting system diagnosis...")
try:
    check_state = start_routines.sr_database_checks()
    if not check_state:
        print("\t- Start routine check failed...")
except Exception as error:
    print("Error raised:", error)
else:
    print("\t- All checks passed.... proceeding...")
    try:
        modems.listen_for_modems()
    except Exception as error:
        print( error)
