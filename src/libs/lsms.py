#!/bin/python
import subprocess

class SMS():
    def __init__(self, index=None, messageID=None):
        self.mmcli_create_sms = ["--messaging-create-sms"]

        self.text = None
        self.index = index
        self.phonenumber = None
        self.validity = None
        self.delivery_report_request = None
        self.messageID=messageID


        # check is index truly exist
        # else raise exception

    def get(self, key):
        return {
                "text" : "sms.content.text", 
                "phonenumber" : "sms.content.phonenumber", 
                "type" : "sms.properties.pdu-type"}[key]

    def list(self, modem):
        sms_list = []
        sms_list += modem.mmcli_m + ["--messaging-list-sms"]

        try: 
            mmcli_output = subprocess.check_output(sms_list, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
            mmcli_output = mmcli_output.split('\n')
            n_modems = int(mmcli_output[0].split(': ')[1])
            # print(f"[=] #modems: {n_modems}")
            sms = []
            for i in range(1, (n_modems + 1)):
                sms_index = mmcli_output[i].split('/')[-1]
                if not sms_index.isdigit():
                    continue
                # print(f"[{i}]: index of>> {modem_index}")
                sms.append( sms_index )

            return sms


    def create_sms(self, phonenumber, text, delivery_report_request :bool=False, validity :int=None):
        # print(f"Text: {text}")
        # print(f"Number: {phonenumber}")

        if self.index != None:
            raise Exception("sms has index, cannot edit")

        else:
            self.text = text
            self.phonenumber = phonenumber
            self.validity = validity
            self.delivery_report_request = delivery_report_request

            return self

    # TODO: Parse the output of this to make it cleaner
    def info(self):
        info = []
        info += ["mmcli", "-Ks", self.index]

        try: 
            mmcli_output = subprocess.check_output(info, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            raise Exception(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
        else:
            # print(f"mmcli_output: {mmcli_output}")
            mmcli_output = mmcli_output.split('\n')
            s_details = {}
            for output in mmcli_output:
                s_detail = output.split(': ')
                if len(s_detail) < 2:
                    continue
                key = s_detail[0].replace(' ', '')
                s_details[key] = s_detail[1]

            return s_details
