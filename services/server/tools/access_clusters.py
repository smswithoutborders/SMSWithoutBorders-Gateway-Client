#!/usr/bin/env python3


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



# probably the credentials from mysql server
admin_auth_key="root"
admin_auth_id="asshole"

afkanerd_server="http://localhost:9000/users"
request_body={"auth_id":admin_auth_id, "auth_key":admin_auth_key, "email":sys.argv[1]}
response = request.post(afkanerd_server, json=request_body)
#TODO check if response came in
response = response.json

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
    create_user_command=f"rabbitmqctl add_user '{user_auth_id}' '{user_auth_key}'"
    output = subprocess.check_output(create_user_command.split(' '), stderr=subprocess.STDOUT).decode('unicode_escape')
    print(f'cli output: {output}')
except subprocess.CalledProcessError as error:
    raise subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)

try:
    # requires sudo privileges
    # First ".*" for configure permission on every entity
    # Second ".*" for write permission on every entity
    # Third ".*" for read permission on every entity
    update_user_permissions=f'rabbitmqctl set_permissions -p "/" "{user_auth_id}" ".*" ".*" ".*"'
    output = subprocess.check_output(update_user_permissions.split(' '), stderr=subprocess.STDOUT).decode('unicode_escape')
    print(f'cli output: {output}')
except subprocess.CalledProcessError as error:
    raise subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)
