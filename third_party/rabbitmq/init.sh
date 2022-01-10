#!/usr/bin/bash
tar -xf installer/../third_party/rabbitmq/rabbitmq-server-generic-unix-3.9.9.tar.xz -C installer/../third_party/rabbitmq/builds/

cp installer/files/rabbitmq-env.conf /home/megamind/Desktop/Afkanerd/SMSWithoutBorders-Gateway-Client/third_party/rabbitmq/builds/rabbitmq_server-3.9.9/etc/rabbitmq/rabbitmq-env.conf