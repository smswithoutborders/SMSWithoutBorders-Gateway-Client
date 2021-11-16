#!/usr/bin/env python3


import os
import sys
import copy
import distro
import configparser

'''resources:
    - https://www.freedesktop.org/software/systemd/man/systemd.unit.html#
'''

SUPPORTED_DISTROS_CLUSTER = ['arch', 'debian']
SUPPORTED_DISTROS_GATEWAY = ['arch', 'debian']

DESCRIPTION="[Maintained by Afkanerd] " 
EXEC = f'+'

distro_systemd_schemas = {

        "default": {
            "Unit": {
                "Description" : DESCRIPTION,
                "After" : "ModemManager.service",
                "Wants" : "ModemManager.service",
                "StartLimitIntervalSec" : "60",
                "StartLimitBurst" : "5",
                "StartLimitAction" : "systemctl reboot"
                },
            "Service": {
                "Type" : "simple",
                "ExecStart": EXEC,
                "Restart" : "on-failure",
                "RestartSec" : "5s"
                },
            "Install": {
                "WantedBy" : "multi-user.target"
                }
        }
}


# Distro init
distro_systemd_schemas_gateway = copy.deepcopy(distro_systemd_schemas)

distro_systemd_schemas_cluster = copy.deepcopy(distro_systemd_schemas)

# print(id(distro_systemd_schemas_gateway))
# print(id(distro_systemd_schemas_cluster))

default_schema_gateway = distro_systemd_schemas_gateway.pop('default')
default_schema_cluster = distro_systemd_schemas_cluster.pop('default')

for dist in SUPPORTED_DISTROS_GATEWAY:
    distro_systemd_schemas_gateway[dist] = default_schema_gateway

for dist in SUPPORTED_DISTROS_CLUSTER:
    distro_systemd_schemas_cluster[dist] = default_schema_cluster

# cluster bindings
for dist in distro_systemd_schemas_gateway:
    distro_systemd_schemas_gateway[dist]['Unit']['Description'] += "SMSWithoutBorders Gateway service"

for dist in distro_systemd_schemas_cluster:
    distro_systemd_schemas_cluster[dist]['Unit']['Description'] += "Deku Cluster service"
    distro_systemd_schemas_cluster[dist]['Unit']['BindsTo'] = "ModemManager.service"

def write_schema(schema, systemd_filepath):
    try:
        with open(systemd_filepath, 'w') as fd_schema:
            schema.write(fd_schema)
    except Exception as error:
        raise error

def populate_config(schema):
    _cp = configparser.ConfigParser()
    _cp.read_dict(schema)
    return _cp

# generates only for required distro
dist = distro.like()
print("Current dist", dist)
if dist in SUPPORTED_DISTROS_GATEWAY:
    schema = distro_systemd_schemas_gateway[dist]
    for section in schema:
        print(f"Gateway[{section}]:")
        print([values for values in schema[section]])

print("")

if dist in SUPPORTED_DISTROS_CLUSTER:
    schema = distro_systemd_schemas_cluster[dist]
    for section in schema:
        print(f"Cluster[{section}]:")
        print([values for values in schema[section]])
    """
    try:
        write_schema(schema, systemd_filepath):
    except Exception as error:
        print(error)
        exit(1)
    """
    exit(0)
else:
    print("Not supported distro:", distro)

    exit(1)
