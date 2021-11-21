#!/usr/bin/env python3


import os
import sys
import copy
import distro
import stat
import pathlib
import configparser

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
                    "TimeoutStartSec" : "3600",
                    # "StartLimitIntervalSec" : "60",
                    # "StartLimitBurst" : "5"
                    # "StartLimitAction" : "systemctl reboot"
                    },
                "Service": {
                    "Type" : "simple",
                    "ExecStart": f"+{path_venv}/bin/python3 {path_main}",
                    "Restart" : "on-failure",
                    "RestartSec" : "10s"
                    },
                "Install": {
                    "WantedBy" : "multi-user.target"
                    }
            }
    }

    # print(distro_systemd_schemas)

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
        # distro_systemd_schemas_gateway[dist]['Unit']['BindsTo'] = "deku_rabbitmq.service"
        distro_systemd_schemas_gateway[dist]['Unit']['Wants'] = "ModemManager.service"
        distro_systemd_schemas_gateway[dist]['Service']['ExecStart'] += " --log=INFO --module=gateway"

    for dist in distro_systemd_schemas_cluster:
        distro_systemd_schemas_cluster[dist]['Unit']['Description'] += "Deku Cluster service"
        distro_systemd_schemas_cluster[dist]['Unit']['BindsTo'] = "ModemManager.service"
        distro_systemd_schemas_cluster[dist]['Service']['ExecStart'] += " --log=INFO --module=cluster"

    def write_schema(schema, systemd_filepath):
        fd_schema = open(systemd_filepath, 'w')
        schema.write(fd_schema)

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
    print(f"configuring for distro: [{dist}]")

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
    else:
        print("Not supported distro:", distro)

def generate_deps():
    def write_scripts(data, script_path):
        fd_script_path = open(script_path, 'w')
        fd_script_path.write(data)
        fd_script_path.close()

    def chmodx_scripts(file):
        st = os.stat(file)
        os.chmod(file, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


    def rabbitmq():
        path_rabbitmq_versions_lock =os.path.join(
                os.path.dirname(__file__), '../third_party/rabbitmq', 'version.lock')
        path_rabbitmq_init_script =os.path.join(
                os.path.dirname(__file__), '../third_party/rabbitmq', 'init.sh')

        versioning_info=None
        with open(path_rabbitmq_versions_lock, 'r') as fd_rabbitmq:
            versioning_info= fd_rabbitmq.read()

        versioning_info = versioning_info.split('\n')
        version = versioning_info[0]
        version_fullpath = versioning_info[1]

        ''' rabbitmq_server-3.9.9'''
        path_rabbitmq_instance = f'{path_rabbitmq_builds}rabbitmq_server-{version}'

        # write init script
        data = "#!/usr/bin/bash\n"
        data += f'tar -xf {path_rabbitmq}{version_fullpath} -C {path_rabbitmq_builds}\n'
        write_scripts(data, path_rabbitmq_init_script)
        chmodx_scripts(path_rabbitmq_init_script)

        return str(
                pathlib.Path(path_rabbitmq_instance).resolve()), str(
                        pathlib.Path(path_rabbitmq_init_script).resolve())

    return rabbitmq()

def customize_rabbitmq(path_rabbitmq_instance, path_rabbitmq_init_script):
    path_rabbitmq_template =os.path.join(
            os.path.dirname(__file__), 'templates', 'rabbitmq.service')

    rmq_template = configparser.ConfigParser(strict=False)
    rmq_template.optionxform = lambda option : option
    rmq_template.read(path_rabbitmq_template)

    path_rabbitmq_service =os.path.join(
            os.path.dirname(__file__), 'files', 'deku_rabbitmq.service')

    rmq_template['Service']['EnvironmentFile'] = str(pathlib.Path(
            path_rabbitmq_instance + rmq_template['Service']['EnvironmentFile']).resolve())

    rmq_template['Service']['WorkingDirectory'] = str(pathlib.Path(
            path_rabbitmq_instance).resolve())

    rmq_template['Service']['ExecStart'] = str(pathlib.Path(
            path_rabbitmq_instance + "/sbin/rabbitmq-server").resolve())

    rmq_template['Service']['ExecStop'] = str(pathlib.Path(
            path_rabbitmq_instance + "/sbin/rabbitmqctl stop").resolve())

    def write_service(template, new_service_path):
        fd_service = open(new_service_path, 'w')
        template.write(fd_service)
    
    def write_file(data, filepath, mode='w'):
        fd_file = open(filepath, mode)
        fd_file.write(data)
        fd_file.close()

    def update_init_file(data, filepath):
        fd_file = open(filepath, 'a+')
        fd_file.write(data)
        fd_file.close()

    write_service(rmq_template, path_rabbitmq_service)
    env_data = "NODENAME=rabbit\n" + \
            f"NODE_IP_ADDRESS=127.0.0.1\n" + \
            f"NODE_PORT=5672\n\n" + \
            f"HOME={path_rabbitmq_instance}/var/lib/rabbitmq\n" + \
            f"LOG_BASE={path_rabbitmq_instance}/var/log/rabbitmq\n" + \
            f"MNESIA_BASE={path_rabbitmq_instance}/var/lib/rabbitmq/mnesia"

    path_rabbitmq_env = rmq_template['Service']['EnvironmentFile']

    path_rmq_env_conf = os.path.join(
        os.path.dirname(__file__), 'files', 'rabbitmq-env.conf')

    write_file(env_data, path_rmq_env_conf)

    path_rabbitmq_init_script =os.path.join(
            os.path.dirname(__file__), '../third_party/rabbitmq', 'init.sh')

    cp_file_data = f'\ncp {path_rmq_env_conf} {rmq_template["Service"]["EnvironmentFile"]}'
    update_init_file(cp_file_data, path_rabbitmq_init_script)

if __name__ == "__main__":
    global path_rabbitmq, path_rabbitmq_builds

    path_rabbitmq=os.path.join(
            os.path.dirname(__file__), '../third_party/rabbitmq', '')

    path_rabbitmq_builds=os.path.join(
            os.path.dirname(__file__), '../third_party/rabbitmq/builds', '')

    generate_systemd()
    path_rabbitmq_instance, path_rabbitmq_init_script = generate_deps()
    customize_rabbitmq(path_rabbitmq_instance, path_rabbitmq_init_script)
