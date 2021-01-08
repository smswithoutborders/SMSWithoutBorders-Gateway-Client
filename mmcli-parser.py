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
            # print(f"[{i}]: index of>> {modem_index}")
            modems.append( modem_index )

        return modems

class Modem():
    def __init__( self, index ):
        self.mmcli_m = ["mmcli", f"-Km", index]

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
    print(f">> Modem[{index}]\n{modem.m()}")
