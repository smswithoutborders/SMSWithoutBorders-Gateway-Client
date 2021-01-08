#!/bin/python
import subprocess
from _sms_ import SMS 

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


    def info(self):
        try: 
            mmcli_output = subprocess.check_output(self.mmcli_m, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
            pass

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
        mmcli_create_sms[-1] += f"'=number={sms.number}, text=\"{sms.text}\"'"
        # print(f"mmcli_create_sms: {mmcli_create_sms}")

        try: 
            mmcli_output = subprocess.check_output(mmcli_create_sms, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            print(f"mmcli_output: {mmcli_output}")
    

    def send_sms(self, sms :SMS):
        self.__create( sms )
