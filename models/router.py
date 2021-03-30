#!/bin/python

import socket
import logging
import requests
from models.lsms import SMS 

class Router:
    def __init__(self, router_url):
        self.router_url = router_url


    @staticmethod
    def is_connected():
        try:
            requests.get("https://mail.google.com").status_code
            return True
        except:
            pass
        return False


    def publish(self, sms: SMS):
        try:
            logging.info(f"Routing to: <<{self.router_url}>>")
            request = requests.post(self.router_url, json={"text":sms.text, "phonenumber":sms.phonenumber, "timestamp":sms.timestamp, "discharge_timestamp":sms.discharge_time})
        except Exception as error:
            raise Exception(error)
            
        return request.text
