#!/bin/python

import subprocess
from subprocess import Popen, PIPE

# from models.libMMCLI_python.lsms import SMS 
from .lsms import SMS

import logging
import threading
import deduce_isp as ISP

class Modem():
    details = {}

    def __init__( self, index:int):
        super().__init__()
        self.mmcli_m = ["mmcli", f"-Km", index]
        self.index = index
        self.extractInfo()

    def __bindObject( self, keys :list, value, _object=None):
        if _object == None:
            _object = {}

        if len(keys) > 1:
            if not keys[0] in _object:
                _object[keys[0]] = {}
            new_object = self.__bindObject(keys[1:], value, _object[keys[0]])
            # print(f"{len(keys)}: {new_object}")
            _object[keys[0]] = new_object
        else:
            _object = {keys[0] : value}
        return _object

    def __appendObject( self, kObject, tObject ):
        try:
            if type(tObject) == type(""):
                return {}
            if list(tObject.keys())[0] in kObject:
                key = list(tObject.keys())[0] 
                new_object = self.__appendObject( kObject[key], tObject[key] )
                # print( new_object )
                if not new_object == {}:
                    kObject.update(new_object)
            else:
                kObject.update(tObject)
        except Exception as error:
            print(f"errtObject: ", tObject, type(tObject))
            print(error, "\n")

        return kObject


    def extractInfo(self, mmcli_output=None):
        try: 
            if mmcli_output == None:
                if hasattr(self, 'mmcli_m' ):
                    mmcli_output = subprocess.check_output(self.mmcli_m, stderr=subprocess.STDOUT).decode('utf-8')
                else:
                    raise Exception(f">> no input available to extract information")
        except subprocess.CalledProcessError as error:
            raise Exception(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
            mmcli_output = mmcli_output.split('\n')
            self.details = {}
            for output in mmcli_output:
                m_detail = output.split(': ')
                if len(m_detail) < 2:
                    continue
                key = m_detail[0].replace(' ', '')
                self.details[key] = m_detail[1]

                indie_keys = key.split('.')
                # tmp_details = self.__bindObject( keys=indie_keys, value=m_detail[1] )
                tmp_details = self.__bindObject( keys=indie_keys, value=m_detail[1] )
                # print("tmp_details>> ", tmp_details)
                self.details = self.__appendObject(self.details, tmp_details)
                # print("self.details>> ", self.details)
                # self.details.update( tmp_details )
            # print("self.details:", self.details)
            return self.details

    def readyState(self):
        self.extractInfo()

        # if m_details[self.operator_code].isdigit() and m_details[self.signal_quality_value].isdigit() and m_details[self.sim] != '--':
        if self.details["modem"]["operator-code"].isdigit() and self.details["modem"]["signal-quality"]["value"].isdigit() and self.details["modem"]["generic"]["sim"] != "--":
            return True
        return False

    
    def __create(self, sms :SMS):
        mmcli_create_sms = []
        mmcli_create_sms += self.mmcli_m + sms.mmcli_create_sms
        mmcli_create_sms[-1] += f'=number={sms.phonenumber},text="{sms.text}",delivery-report-request=\'yes\''
        try: 
            mmcli_output = subprocess.check_output(mmcli_create_sms, stderr=subprocess.STDOUT).decode('utf-8').replace('\n', '')

        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
            raise Exception(error)
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
        logging.info(f"{self.details['modem.3gpp.imei']}::{self.index} - Sending SMS:<{sms.text}>")
        mmcli_send = self.mmcli_m + ["-s", sms.index, "--send", "--timeout=10"] 
        print("mmcli:", mmcli_send)
        message=""
        status=""
        try: 
            mmcli_output = subprocess.check_output(mmcli_send, stderr=subprocess.STDOUT).decode('utf-8').replace('\n', '')

        except subprocess.CalledProcessError as error:
            returncode = error.returncode
            err_output = error.output.decode('utf-8').replace('\n', '')
            '''
            print(f">> failed to send sms")
            print(f"\treturn code: {returncode}")
            '''
            print(f"\tstderr: {err_output}")

            # raise Exception( error )
            message=err_output
            return {"state":False, "message":message, "status":"failed", "returncode":returncode}
        else:
            message=mmcli_output
            print(f"{mmcli_output}")
            return {"state":True, "message":message, "status":"sent"}
            

    def set_sms(self, sms :SMS):
        # print("Setting SMS...")
        sms = self.__create( sms )
        return sms



    def send_sms(self, sms :SMS, text=None, receipient=None):
        send_status=None
        try:
            send_status=self.__send( sms )
        except Exception as error:
            raise Exception(error)

        return send_status


    def get_received_messages(self):
        lsms = SMS().get_messages(self)
        sms_received = []
        for sms in lsms:
            sms.extract_message()
            if sms.state == "received" and (sms.details["sms.properties.pdu-type"] == "deliver" or sms.details["sms.properties.pdu-type"] == "status-report"):
                sms_received.append( sms )

        return sms_received

    def remove_sms(self, sms :SMS):
        mmcli_delete_sms = self.mmcli_m 
        mmcli_delete_sms += [f"--messaging-delete-sms={sms.index}"] 
        try: 
           mmcli_output = subprocess.check_output(mmcli_delete_sms, stderr=subprocess.STDOUT).decode('utf-8').replace('\n', '')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
            raise Exception(error)
        else:
            # print(f"{mmcli_output}")
            return True
