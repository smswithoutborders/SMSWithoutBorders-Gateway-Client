#!/usr/bin/bash
tar -xf /home/sherlock/Desktop/afkanerd/SMSWithoutBorders-Gateway-Client/installer/../deps/rabbitmq/rabbitmq-server-generic-unix-3.9.9.tar.xz -C /home/sherlock/Desktop/afkanerd/SMSWithoutBorders-Gateway-Client/installer/../deps/rabbitmq/builds/

cp /home/sherlock/Desktop/afkanerd/SMSWithoutBorders-Gateway-Client/installer/files/rabbitmq-env.conf /home/sherlock/Desktop/afkanerd/SMSWithoutBorders-Gateway-Client/deps/rabbitmq/builds/rabbitmq_server-3.9.9/etc/rabbitmq/rabbitmq-env.conf