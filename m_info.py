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

    if not modem.ready_state():
        continue

    sms = SMS()
    sms = sms.create_sms("00000", "sample sms message")
    sms = modem.set_sms( sms )
    # print(f"sms info: {sms.info()}]")

    for sms_index in sms.list(modem):
        _sms = SMS()
        _sms.index = sms_index
        # print(_sms.info())
        sms_details = _sms.info()
        print(f"[=]SMS text: {sms_details[_sms.get('text')]}")
        print(f"[=]SMS type: {sms_details[_sms.get('type')]}")
        print(f"[=]SMS number: {sms_details[_sms.get('number')]}")
        print()
    
    try:
        send_status = modem.send_sms( sms )
        print(f"[=]SMS sent: {send_status}")
    except Exception as error:
        print( error )
