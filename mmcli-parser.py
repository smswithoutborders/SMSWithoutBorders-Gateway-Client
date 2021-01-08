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


modems = Modems()
print(f">>Modems indexes: {modems.L()}")
