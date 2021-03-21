#!/bin/python
import subprocess

class SMS():
    def __init__(self, index=None, messageID=None):
        self.mmcli_create_sms = ["--messaging-create-sms"]

        self.text = None
        self.state = None
        self.index = index
        self.validity = None
        self.timestamp = None
        self.phonenumber = None
        self.messageID=messageID
        self.discharge_time = None
        self.delivery_report_request = None


        # check is index truly exist
        # else raise exception

    def get(self, key):
        return {
                "text" : "sms.content.text", 
                "phonenumber" : "sms.content.phonenumber", 
                "type" : "sms.properties.pdu-type"}[key]

    def __list(self, modem):
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

    def extract_message(self):
        sms_info = ["mmcli", "-Ks", self.index]
        try: 
            mmcli_output = subprocess.check_output(sms_info, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
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
            self.text = self.details["sms.content.text"]
            self.state = self.details["sms.properties.state"]
            self.phonenumber = self.details["sms.content.number"]
            self.timestamp = self.details["sms.properties.timestamp"]
            self.discharge_time = self.details["sms.properties.discharge-timestamp"]
            return self.details


    def get_messages(self, modem):
        sms_indexes = self.__list(modem)
        lsms = []
        for index in sms_indexes:
            sms = SMS(index=index)
            lsms.append( sms )

        return lsms


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
