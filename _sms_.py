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
        print(f"Text: {text}")
        print(f"Number: {number}")

        if self.index != None:
            raise Exception("sms has index, cannot edit")

        else:
            self.text = text
            self.number = number
            self.validity = validity
            self.delivery_report_request = delivery_report_request
