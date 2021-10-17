#!/usr/bin/env python3

import sys, os
import requests
import configparser


def make_request(url, auth_id, auth_key, user_id, project_id, isp, number):
    request={"auth_id":auth_id, "auth_key":auth_key, "user_id":user_id, "project_id":project_id, "data":[{"text":"Hello world", "number":number, "isp":isp}]}
    response = requests.post(url=url, json=request)
    print(response.text, response.status_code)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: ./requests.py [user id] [project id] [isp] [number]")
    else:
        config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        config.read(os.path.join(os.path.dirname(__file__), '../configs', 'config.ini'))

        user_id=sys.argv[1]
        project_id=sys.argv[2]
        isp=sys.argv[3]
        number=sys.argv[4]

        auth_id=config['NODE']['api_id']
        auth_key=config['NODE']['api_key']
        url="http://" + config['NODE']['connection_url'] + ":15673/sms"

        make_request(url, auth_id, auth_key, user_id, project_id, isp, number)
