#!/bin/python

import subprocess
from _sms_ import SMS 
from modems import Modems 
from modem import Modem 

''' modems.py
- Acquire all plugged in modems
- Acquire specific modem
'''

''' modem.py
- Acquire modem's details
'''

modems = Modems()
print(f">>Modems indexes: {modems.list()}")
for index in modems.list():
    modem = Modem( index )
    modem_m = modem.info()
    print(f"\n>> Modem[{index}]")
    print(f"[=]Modem-state: [{modem_m[modem.state]}]")
    print(f"[=]Modem-operator-name: [{modem_m[modem.operator_name]}]")
    print(f"[=]Modem-operator-code: [{modem_m[modem.operator_code]}]")
    print(f"[=]Modem-ready-state: [{modem.ready_state()}]")

    sms = SMS()
    sms.create_sms("0000", "sample sms message")
    sms_state = modem.send_sms( sms )
