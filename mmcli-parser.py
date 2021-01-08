#!/bin/python

import subprocess

''' modems.py
- Acquire all plugged in modems
- Acquire specific modem
'''

class Modems():
    def __init__( self ):
        self.mmcli_L = ["mmcli", "-KL"]

    def L( self ):
        mmcli_output = subprocess.check_output(self.mmcli_L).decode('utf-8')
        mmcli_output = mmcli_output.split('\n')

        n_modems = int(mmcli_output[0].split(': ')[1])
        # print(f"[=] #modems: {n_modems}")
        modems = []
        for i in range(1, (n_modems + 1)):
            modem_index = mmcli_output[i].split('/')[-1]
            if not modem_index.isdigit():
                continue
            # print(f"[{i}]: index of>> {modem_index}")
            modems.append( modem_index )

        return modems

class Modem():
    def __init__( self, index ):
        self.mmcli_m = ["mmcli", f"-Km", index]

        # Modem parse keys
        self.imei = "modem.3gpp.imei"
        self.sim = "modem.generic.sim"
        self.state = "modem.generic.state"
        self.device = "modem.generic.device"
        self.operator_code = "modem.3gpp.operator-code"
        self.operator_name = "modem.3gpp.operator-name"
        self.primary_port = "modem.generic.primary-port"
        self.device_identifier = "modem.generic.device-identifier"
        self.state_failed_reason = "modem.generic.state-failed-reason"
        self.equipment_identifier = "modem.generic.equipment-identifier"
        self.signal_quality_value = "modem.generic.signal-quality.value"
        self.access_technologies_values = "modem.generic.access-technologies.value[1]"

    def m(self):
        mmcli_output = subprocess.check_output(self.mmcli_m).decode('utf-8')
        mmcli_output = mmcli_output.split('\n')

        m_details = {}
        for output in mmcli_output:
            m_detail = output.split(': ')
            if len(m_detail) < 2:
                continue
            m_details[m_detail[0].replace(' ', '')] = m_detail[1]

        return m_details


modems = Modems()
print(f">>Modems indexes: {modems.L()}")
for index in modems.L():
    modem = Modem( index )
    modem_m = modem.m()
    print(f">> Modem[{index}]")
    print(f"modem.gener{modem_}")
