#!/bin/python

import socket
import logging
import requests
from libMMCLI_python.lsms import SMS 

class Router:
    def __init__(self, router_url):
        self.router_url = router_url


    @staticmethod
    def is_connected():
        try:
            requests.get("https://mail.google.com", timeout=5).status_code
            return True
        except:
            pass
        return False


    def publish(self, sms: SMS):
        try:
            logging.info(f"Routing to: <<{self.router_url}>>")
            request = requests.post(self.router_url, json={"text":sms.text, "phonenumber":sms.phonenumber, "timestamp":sms.timestamp, "discharge_timestamp":sms.discharge_time}, verify=False)

            request = request.json()
            if 'status' in request:
                if request['status'] != 200:
                    # Log the reason for the failure here
                    print(request)
                    return False
                else:
                    return True

        except Exception as error:
            raise Exception(error)
        else:
            return False
