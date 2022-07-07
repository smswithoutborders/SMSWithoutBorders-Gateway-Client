#!/usr/bin/env python3


import os
import getpass
import sys
import copy
import distro
import stat
import pathlib
import configparser
import logging

'''resources:
    - https://www.freedesktop.org/software/systemd/man/systemd.unit.html#
'''

SUPPORTED_DISTROS_CLUSTER = ['arch', 'debian']
SUPPORTED_DISTROS_GATEWAY = ['arch', 'debian']

path_main =os.path.join(os.path.dirname(__file__), '../src', 'main.py')
path_venv =os.path.join(os.path.dirname(__file__), '../venv', '')

path_main = str(pathlib.Path(path_main).resolve())
path_venv = str(pathlib.Path(path_venv).resolve())

def generate_systemd():
    distro_systemd_schemas = {

            "default": {
                "Unit": {
                    "Description" : "",
                    "After" : "ModemManager.service",
                    },
                "Service": {
                    "Type" : "simple",
                    "ExecStart": "",
                    "Restart" : "on-failure",
                    "RestartSec": "1",
                    "User":"root",
                    },
                "Install": {
                    "WantedBy" : "multi-user.target"
                    }
            }
    }

    # print(distro_systemd_schemas)

    # Distro init
    distro_systemd_schemas_inbound = copy.deepcopy(distro_systemd_schemas)

    distro_systemd_schemas_outbound = copy.deepcopy(distro_systemd_schemas)

    # print(id(distro_systemd_schemas_inbound))
    # print(id(distro_systemd_schemas_outbound))

    default_schema_gateway = distro_systemd_schemas_inbound.pop('default')
    default_schema_cluster = distro_systemd_schemas_outbound.pop('default')

    for dist in SUPPORTED_DISTROS_GATEWAY:
        distro_systemd_schemas_inbound[dist] = default_schema_gateway

    for dist in SUPPORTED_DISTROS_CLUSTER:
        distro_systemd_schemas_outbound[dist] = default_schema_cluster

    # cluster bindings
    for dist in distro_systemd_schemas_inbound:
        distro_systemd_schemas_inbound[dist]['Unit']['Description'] = "SMSWithoutBorders Gateway service - Incoming SMS (inbound)"
        distro_systemd_schemas_inbound[dist]['Unit']['Wants'] = "ModemManager.service"
        distro_systemd_schemas_inbound[dist]['Service']['ExecStart'] = \
                f"+{path_venv}/bin/python3 {path_main} --log=DEBUG --module=inbound"

    for dist in distro_systemd_schemas_outbound:
        distro_systemd_schemas_outbound[dist]['Unit']['Description'] = "SMSWithoutBorders Gateway service - Outgoing SMS (outbound)"
        distro_systemd_schemas_outbound[dist]['Unit']['BindsTo'] = "ModemManager.service"
        distro_systemd_schemas_outbound[dist]['Service']['ExecStart'] = \
                f"+{path_venv}/bin/python3 {path_main} --log=DEBUG --module=outbound"

    def write_schema(schema, systemd_filepath):
        fd_schema = open(systemd_filepath, 'w')
        schema.write(fd_schema)

    def populate_config(schema):
        _cp = configparser.ConfigParser(strict=False, interpolation=None)
        _cp.optionxform = lambda option: option
        _cp.read_dict(schema)
        return _cp

    # generates only for required distro
    systemd_filepath_inbound = os.path.join(
            os.path.dirname(__file__), 'files', 'swob_inbound.service')

    systemd_filepath_outbound = os.path.join(
            os.path.dirname(__file__), 'files', 'swob_outbound.service')

    dist = distro.like()
    print(f"configuring for distro: [{dist}]")

    if dist in SUPPORTED_DISTROS_GATEWAY:
        schema = distro_systemd_schemas_inbound[dist]
        """
        for section in schema:
            print(f"Gateway[{section}]:")
            print([values for values in schema[section]])
        """
        try:
            write_schema(populate_config(schema), systemd_filepath_inbound)
        except Exception as error:
            print(error)
            exit(1)

    if dist in SUPPORTED_DISTROS_CLUSTER:
        schema = distro_systemd_schemas_outbound[dist]
        """
        for section in schema:
            print(f"Cluster[{section}]:")
            print([values for values in schema[section]])
        """
        try:
            write_schema(populate_config(schema), systemd_filepath_outbound)
        except Exception as error:
            print(error)
    else:
        print("Not supported distro:", distro)


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')

    generate_systemd()
