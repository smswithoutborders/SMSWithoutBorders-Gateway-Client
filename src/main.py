#!/usr/bin/env python3


import os
import sys
import logging
import threading
import argparse

import node
import gateway
from common.CustomConfigParser.customconfigparser import CustomConfigParser


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument(
            '-l', '--log', 
            default='INFO', 
            help='--log=[DEBUG, INFO, WARNING, ERROR, CRITICAL]')

    parser.add_argument("-m", "--module", 
            nargs='?',
            default="all",
            help="node, gateway, all")

    args = parser.parse_args()

    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    logging.basicConfig(
            format='%(asctime)s|[%(levelname)s] %(pathname)s %(lineno)d|%(message)s',
            # datefmt='%Y-%m-%d %I:%M:%S %p',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler('src/services/logs/service.log'),
                logging.StreamHandler(sys.stdout) ],
            encoding='utf-8',
            level=args.log.upper())

    formatter = logging.Formatter('%(asctime)s|[%(levelname)s] %(pathname)s %(lineno)d|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    try:
        configreader=CustomConfigParser(os.path.join(os.path.dirname(__file__), '..', ''))
        config=configreader.read(".configs/config.ini")
        config_event_rules=configreader.read(".configs/events/rules.ini")
        config_isp_default = configreader.read('.configs/isp/default.ini')
        config_isp_operators = configreader.read('.configs/isp/operators.ini')
    except Exception as error:
        logging.critical(error)

    try:
        if args.module == "node" or args.module == "all":
            node_thread = threading.Thread(target=node.main, 
                    args=(config, config_event_rules, config_isp_default, config_isp_operators,),
                    daemon=True)


            node_thread.start()

        if args.module == "gateway" or args.module == "all":
            gateway_thread = threading.Thread(target=gateway.main, 
                    args=(config, config_event_rules, config_isp_default, config_isp_operators,),
                    daemon=True)

            gateway_thread.start()

        if args.module == "node" or args.module == "all":
            node_thread.join()
        if args.module == "gateway" or args.module == "all":
            gateway_thread.join()
    except Exception as error:
        logging.critical(error)
