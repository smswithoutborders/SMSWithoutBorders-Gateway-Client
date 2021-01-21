#!/bin/python
import subprocess
from subprocess import Popen, PIPE
from _sms_ import SMS 
import logging
import threading

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


    def listen_for_sms(self, mutex):
        # Dependency, checks if MySQL is installed on the system
        # logging.info(f"{self.mmcli_m}")
        # TODO: Can begin checking for sms messages wherever there are
        try:
            mutex.acquire()
            logging.info(f"[{self.info()[self.imei]}]: Modem output")
            try:
                pending_request = db_connector.get_pending_request()
                if len(pending_request) < 1:
                    logging.info(f"")
                else:
                    # update the db
                    pass
            except mysql.connector.Error as err:
                raise Exception( err )
        except Exception as error:
            raise Exception( error )

        mutex.release()
        # print( mutex )
            

    def info(self):
        try: 
            mmcli_output = subprocess.check_output(self.mmcli_m, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            raise Exception(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
            mmcli_output = mmcli_output.split('\n')
            m_details = {}
            for output in mmcli_output:
                m_detail = output.split(': ')
                if len(m_detail) < 2:
                    continue
                m_details[m_detail[0].replace(' ', '')] = m_detail[1]
            return m_details


    def ready_state(self):
        m_details = self.info()
        if m_details[self.operator_code].isdigit() and m_details[self.signal_quality_value].isdigit() and m_details[self.sim] != '--':
            return True
        return False

    
    def __create(self, sms :SMS):
        mmcli_create_sms = []
        mmcli_create_sms += self.mmcli_m + sms.mmcli_create_sms
        mmcli_create_sms[-1] += '=number=' + sms.number + ",text='" + sms.text + "'"
        try: 
            mmcli_output = subprocess.check_output(mmcli_create_sms, stderr=subprocess.STDOUT).decode('utf-8').replace('\n', '')

        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            print(f"{mmcli_output}")
            mmcli_output = mmcli_output.split(': ')
            creation_status = mmcli_output[0]
            sms_index = mmcli_output[1].split('/')[-1]
            if not sms_index.isdigit():
                print(f">> sms index isn't an index: {sms_index}")
            else:
                sms.index = sms_index
                # self.__send(sms)
        return sms

    def __send(self, sms: SMS):
        mmcli_send = self.mmcli_m + ["-s", sms.index, "--send"]
        try: 
            mmcli_output = subprocess.check_output(mmcli_send, stderr=subprocess.STDOUT).decode('utf-8').replace('\n', '')

        except subprocess.CalledProcessError as error:
            returncode = error.returncode
            err_output = error.output.decode('utf-8').replace('\n', '')
            print(f">> failed to send sms")
            print(f"\treturn code: {returncode}")
            print(f"\tstderr: {err_output}")
            # raise Exception( error )
        else:
            print(f"{mmcli_output}")
            return True


    def set_sms(self, sms :SMS):
        self.sms = self.__create( sms )
        return self.sms

    def send_sms(self, sms :SMS):
        return self.__send( sms )
