#!/usr/bin/env python3

import json
import sys, os
import requests
import subprocess
import configparser

""" This tool should be ran on a server """
""" Requires sudo to run """

'''
- users need an Afkanerd credential 
- then the credentials are used to provide access 
    to the cluster account.
    - Username = AUTH_ID
    - Password = AUTH_KEY
'''

#TODO create user to the afkanerd servers and get id and key
#TODO use id and key to create rabbitmq credentials (once user gets this details they can log in)
#TODO use credentials on Nodes and they can now connect to the server

config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
# probably the credentials from mysql server
# acquire the keys once you create the admin
admin_auth_key=config['ADMIN']['auth_key']
admin_auth_id=config['ADMIN']['auth_id']

afkanerd_server=f"{config['AUTHENTICATION']['URL']}/users"
request_body={"auth_id":admin_auth_id, "auth_key":admin_auth_key, "email":sys.argv[1], "password":sys.argv[2]}
response = requests.post(afkanerd_server, json=request_body)
#TODO check if response came in
# print(response.text)
response = response.json()
print(response)

user_id=response['id']
user_auth_key=response['auth_key']
user_auth_id=response['auth_id']


''' dev tool runs on the server '''
'''
rabbitmqctl add_user 'username' '2a55f70a841f18b97c3a7db939b7adc9e34a0f1b'
'''

# create user
try:
    # requires sudo privileges
    # First ".*" for configure permission on every entity
    # Second ".*" for write permission on every entity
    # Third ".*" for read permission on every entity
    create_user_command=f"rabbitmqctl add_user {user_auth_id} {user_auth_key}"
    output = subprocess.check_output(create_user_command.split(' '), stderr=subprocess.STDOUT).decode('unicode_escape')
    print(f'cli output: {output}')
except subprocess.CalledProcessError as error:
    # raise subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)
    print(error.output)

try:
    # requires sudo privileges
    # First ".*" for configure permission on every entity
    # Second ".*" for write permission on every entity
    # Third ".*" for read permission on every entity
    # update_user_permissions=f'rabbitmqctl set_permissions -p "/" "{user_auth_id}" ".*" ".*" ".*"'
    update_user_permissions=f'rabbitmqctl set_permissions -p / {user_auth_id} .* .* .*'
    # user_permission_split=update_user_permissions.split(' ')
    # print(user_permission_split)
    output = subprocess.check_output(update_user_permissions.split(' '), stderr=subprocess.STDOUT).decode('unicode_escape')
    print(f'cli output: {output}')
except subprocess.CalledProcessError as error:
    # subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)
    print(error.output)
