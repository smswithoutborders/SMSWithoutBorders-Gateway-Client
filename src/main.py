#!/usr/bin/env python3


import os
import sys
import logging
import threading
import argparse
import traceback

# import node
# import gateway
import incoming
from modem_manager import ModemManager
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
            help="cluster, gateway, all")

    args = parser.parse_args()

    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    log_file_path = os.path.join(os.path.dirname(__file__), 'services/logs', 'service.log')
    logging.basicConfig(
            # format='%(asctime)s|[%(levelname)s] %(pathname)s %(lineno)d|%(message)s',
            format='%(asctime)s|[%(levelname)s] [%(module)s] %(message)s',
            # datefmt='%Y-%m-%d %I:%M:%S %p',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler(sys.stdout) ],
            # encoding='utf-8',
            level=args.log.upper())

    formatter = logging.Formatter('%(asctime)s|[%(levelname)s] %(pathname)s %(lineno)d|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    try:
        configreader=CustomConfigParser(os.path.join(os.path.dirname(__file__), '..', ''))
        config=configreader.read(".configs/config.ini")
        config_event_rules=configreader.read(".configs/events/rules.ini")
        config_isp_default = configreader.read('.configs/isp/default.ini')
        config_isp_operators = configreader.read('.configs/isp/operators.ini')
        third_party_paths = config.read('deps/.configs/paths.ini')
    except Exception as error:
        logging.critical(traceback.format_exc())

    try:
        modemManager = ModemManager()
    except Exception as error:
        logging.exception(error)
    else:
        try:
            if args.module == "incoming" or args.module == "all":
                th_incoming = threading.Thread(target=incoming.main, 
                        args=(modemManager,),
                        daemon=True)

                th_incoming.start()
                th_incoming.join()

            """
            if args.module == "outgoing" or args.module == "all":
                '''
                gateway_thread = threading.Thread(target=gateway.main, 
                        args=(config, config_event_rules, config_isp_default, config_isp_operators,),
                        daemon=True)

                gateway_thread.start()
                '''
                # modemManager.init_daemon(model=gatewayIncoming)
                pass

            if args.module == "cluster" or args.module == "all":
                node_thread.join()
            if args.module == "gateway" or args.module == "all":
                gateway_thread.join()
            """
        except Exception as error:
            logging.critical(traceback.format_exc())
