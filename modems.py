#!/bin/python
import subprocess
import threading
from modem import Modem 
import time

# TODO: Listen for modems and use events
class Modems():
    def __init__( self ):
        self.mmcli_L = ["mmcli", "-KL"]
        self.mutex = threading.Lock()

    def list( self ):
        try: 
            mmcli_output = subprocess.check_output(self.mmcli_L, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
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

    def listen_for_modems( self ):
        # TODO: Get list of modems, keep monitoring list.
        # TODO: If list changes (size or content), check for change 
        p_l_modems = []
        while True:
            l_modems = self.list()
            p_l_modems = l_modems

            for modem_index in l_modems:
                modem = Modem( modem_index)
                t_modem = threading.Thread(target=modem.listen_for_sms, args=(self.mutex,), daemon=False)
                t_modem.start()
            time.sleep( 5 )

        
