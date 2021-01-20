#!/bin/python

import subprocess
from _sms_ import SMS 
from modem import Modem 
from modems import Modems 

# Beginning daemon from here
modems = Modems()
modems.listen_for_modems()
