#!/bin/python
import subprocess
import threading
if __name__ == "__main__":
    from modem import Modem 
else:
    from modules.modem import Modem 
import time
import logging

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
        no_modem_shown = False

        format = "[%(asctime)s] >> %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
        while True:
            l_modems = self.list()
            if len(l_modems) == 0 and not no_modem_shown:
                    logging.info(f">> No modem found")
                    no_modem_shown = True
                    continue
            modem_claims = {}
            for modem_index in l_modems:
                no_modem_shown = False
                modem = Modem( modem_index)
                if not modem_index in p_l_modems:
                    logging.info(f"[+] New modem found: [{modem.info()[modem.operator_code]}:{modem_index}]")

                # Threading is bad architecture for here
                '''
                t_modem = threading.Thread(target=modem.listen_for_sms, args=(self.mutex,), daemon=False)
                try:
                    t_modem.start()
                except Exception as err:
                    logger.error( err )
                '''
                id_sms = modem.claim_sms()
                if not id_sms == None:
                    modem_claims[modem.info()[modem.imei]] = id_sms
            

            p_l_modems = l_modems
            time.sleep( 5 )
