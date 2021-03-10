#!/bin/python
import subprocess
import threading
from modules.modem import Modem 
import time
import logging

# TODO: Listen for modems and use events
class Modems():
    def __init__( self ):
        self.mmcli_L = ["mmcli", "-KL"]
        self.mutex = threading.Lock()

    def claim( self, modem: Modem ):
        pass

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
        prev_list_of_modems = []
        fl_no_modem_shown = False

        format = "[%(asctime)s] >> %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")


        while True:
            list_of_modems = self.list()

            if len(list_of_modems) == 0 and not no_modem_shown:
                    logging.info("No modem found...")
                    fl_no_modem_shown = True
                    continue

            for modem_index in list_of_modems:
                fl_no_modem_shown = False

                modem = Modem( modem_index)
                if not modem.ready_state():
                    continue

                if not modem_index in prev_list_of_modems:
                    logging.info(f"[+] New modem found: [{modem.info()[modem.operator_code]}:{modem_index}]")

            prev_list_of_modems = list_of_modems
            time.sleep( 5 )
