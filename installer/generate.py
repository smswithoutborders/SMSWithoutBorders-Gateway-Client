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

path_main =os.path.join(os.path.dirname(__file__), '../src', 'main.py')
path_venv =os.path.join(os.path.dirname(__file__), '../venv', '')

distro_systemd_schemas = {

        "default": {
            "Unit": {
                "Description" : "",
                "After" : "ModemManager.service",
                "Wants" : "ModemManager.service",
                "StartLimitIntervalSec" : "60",
                "StartLimitBurst" : "5"
                # "StartLimitAction" : "systemctl reboot"
                },
            "Service": {
                "Type" : "simple",
                "ExecStart": f"+{path_venv}bin/python3 {path_main}",
                "Restart" : "on-failure",
                "RestartSec" : "5s"
                },
            "Install": {
                "WantedBy" : "multi-user.target"
                }
        }
}

print(distro_systemd_schemas)


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
    _cp = configparser.ConfigParser(strict=False)
    _cp.optionxform = lambda option: option
    _cp.read_dict(schema)
    return _cp

# generates only for required distro
systemd_filepath_gateway = os.path.join(
        os.path.dirname(__file__), 'files', 'deku_gateway.service')

systemd_filepath_cluster = os.path.join(
        os.path.dirname(__file__), 'files', 'deku_cluster.service')

dist = distro.like()
print(f"Current dist [{dist}]")

if dist in SUPPORTED_DISTROS_GATEWAY:
    schema = distro_systemd_schemas_gateway[dist]
    """
    for section in schema:
        print(f"Gateway[{section}]:")
        print([values for values in schema[section]])
    """
    try:
        write_schema(populate_config(schema), systemd_filepath_gateway)
    except Exception as error:
        print(error)
        exit(1)
    exit(0)

print("")

if dist in SUPPORTED_DISTROS_CLUSTER:
    schema = distro_systemd_schemas_cluster[dist]
    """
    for section in schema:
        print(f"Cluster[{section}]:")
        print([values for values in schema[section]])
    """
    try:
        write_schema(populate_config(schema), systemd_filepath_cluster)
    except Exception as error:
        print(error)
        exit(1)
    exit(0)

else:
    print("Not supported distro:", distro)

    exit(1)
