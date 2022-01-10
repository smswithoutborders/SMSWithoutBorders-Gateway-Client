#!/usr/bin/bash
tar -xf /home/sherlock/Desktop/SMSWithoutBorders-Gateway-Client/installer/../third_party/rabbitmq/rabbitmq-server-generic-unix-3.9.9.tar.xz -C /home/sherlock/Desktop/SMSWithoutBorders-Gateway-Client/installer/../third_party/rabbitmq/builds/

cp /home/sherlock/Desktop/SMSWithoutBorders-Gateway-Client/installer/files/rabbitmq-env.conf /home/sherlock/Desktop/SMSWithoutBorders-Gateway-Client/third_party/rabbitmq/builds/rabbitmq_server-3.9.9/etc/rabbitmq/rabbitmq-env.conf