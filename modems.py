#!/bin/python
import subprocess

class Modems():
    def __init__( self ):
        self.mmcli_L = ["mmcli", "-KL"]

    def list( self ):
        try: 
            mmcli_output = subprocess.check_output(self.mmcli_L, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
            pass

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


