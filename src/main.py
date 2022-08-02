#!/usr/bin/env python3

"""
https://www.freedesktop.org/software/ModemManager/api/latest/gdbus-org.freedesktop.ModemManager1.Modem.Messaging.html#gdbus-signal-org-freedesktop-ModemManager1-Modem-Messaging.Added
"""


import os
import sys
import logging
import threading
import argparse
import configparser

import inbound as Inbound
import outbound as Outbound

from modem_manager import ModemManager


def main_inbound(modem_manager: ModemManager) -> None:
    """
    """
    configs = configparser.ConfigParser(interpolation=None)
    configs.read(
            os.path.join(os.path.dirname(__file__),
                '../.configs', 'config.ini'))

    Inbound.Main(modem_manager=modem_manager, configs=configs)


def main_outbound(modem_manager: ModemManager) -> None:
    """
    """
    configs = configparser.ConfigParser()
    configs.read(
            os.path.join(os.path.dirname(__file__),
                '../.configs', 'config.ini'))

    Outbound.Main(modem_manager=modem_manager, configs=configs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument(
            '-l', '--log', 
            default='INFO', 
            help='--log=[DEBUG, INFO, WARNING, ERROR, CRITICAL]')

    parser.add_argument("-m", "--module", 
            nargs='?',
            default="all",
            help="outbound, inbound, all")

    args = parser.parse_args()

    # https://docs.python.org/3/library/logging.html#logrecord-attributes

    log_file_path = os.path.join(
            os.path.dirname(__file__), 'services/logs', 'service.log')

    # handler= [logging.FileHandler(log_file_path), logging.StreamHandler(sys.stdout) ]


    # datefmt='%Y-%m-%d %H:%M:%S',
    datefmt='%H:%M:%S'
    format_= "[%(levelname)s] [%(thread)d:%(threadName)s]| " + \
            "[%(module)s] %(message)s"

    logging.basicConfig(
            format=format_,
            datefmt=datefmt,
            level=args.log.upper())

    try:

        logging.info("")
        modem_manager = ModemManager()

    except Exception as error:
        logging.exception(error)
    else:
        if args.module == "inbound":
            try:
                main_inbound(modem_manager)
            except Exception as error:
                logging.exception(error)


        elif args.module == "outbound":
            try:
                main_outbound(modem_manager)
            except Exception as error:
                logging.exception(error)

        modem_manager.daemon()
