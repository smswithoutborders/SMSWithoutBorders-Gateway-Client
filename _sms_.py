#!/bin/python
import subprocess

class SMS():
    def __init__(self, index=None):
        self.mmcli_create_sms = ["--messaging-create-sms"]

        self.text = None
        self.index = index
        self.number = None
        self.validity = None
        self.delivery_report_request = None

        # check is index truly exist
        # else raise exception

    def create_sms(self, number, text, delivery_report_request=False, validity=None):
        # print(f"Text: {text}")
        # print(f"Number: {number}")

        if self.index != None:
            raise Exception("sms has index, cannot edit")

        else:
            self.text = text
            self.number = number
            self.validity = validity
            self.delivery_report_request = delivery_report_request

    # TODO: Parse the output of this to make it cleaner
    def info(self):
        info = []
        info += ["mmcli", "-s", self.index]
        try: 
            mmcli_output = subprocess.check_output(info, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as error:
            print(f"[stderr]>> return code[{error.returncode}], output[{error.output.decode('utf-8')}")
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
