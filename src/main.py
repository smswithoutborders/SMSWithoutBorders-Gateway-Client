#!/usr/bin/env python3


import os
import sys
import logging
import threading
import argparse
import configparser

import inbound

import outbound

from modem_manager import ModemManager


def start_thread_inbound(modem_manager: ModemManager):
    """
    """
    configs = configparser.ConfigParser(interpolation=None)
    configs.read(
            os.path.join(os.path.dirname(__file__),
                '../.configs', 'config.ini'))

    inbound_thread = threading.Thread(target=inbound.main, 
            kwargs={"modem_manager":modem_manager, "configs": configs}, daemon=True)

    inbound_thread.start()

    return inbound_thread


def start_thread_outbound(modem_manager: ModemManager):
    """
    """
    configs = configparser.ConfigParser()
    configs.read(
            os.path.join(os.path.dirname(__file__),
                '../.configs', 'config.ini'))

    outbound_thread = threading.Thread(target=outbound.main, 
            kwargs={"modem_manager":modem_manager, "configs": configs}, daemon=True)

    outbound_thread.start()

    return outbound_thread



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
    log_file_path = os.path.join(os.path.dirname(__file__), 'services/logs', 'service.log')
    logging.basicConfig(
            format='%(asctime)s|[%(levelname)s] [%(module)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler(sys.stdout) ],
            level=args.log.upper())

    try:
        modem_manager = ModemManager()
    except Exception as error:
        logging.exception(error)
    else:
        try:
            inbound_thread = start_thread_inbound(modem_manager)
        except Exception as error:
            logging.exception(error)

        try:
            outbound_thread = start_thread_outbound(modem_manager)
        except Exception as error:
            logging.exception(error)

        modem_manager.daemon()
