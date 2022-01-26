#!/usr/bin/env python3


import os
import sys
import logging
import threading
import argparse
import traceback

import incoming
import outgoing
from modem_manager import ModemManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument(
            '-l', '--log', 
            default='INFO', 
            help='--log=[DEBUG, INFO, WARNING, ERROR, CRITICAL]')

    parser.add_argument("-m", "--module", 
            nargs='?',
            default="all",
            help="incoming, outgoing, all")

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

    formatter = logging.Formatter('%(asctime)s|[%(levelname)s] %(pathname)s %(lineno)d|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    try:
        modemManager = ModemManager()
    except Exception as error:
        logging.exception(error)
    else:
        try:

            if args.module == "outgoing" or args.module == "all":
                th_incoming = threading.Thread(target=outgoing.main, 
                        args=(modemManager,))

                th_incoming.start()
                if not args.module == "all":
                    th_incoming.join()
                    modemManager.daemon()

            if args.module == "incoming" or args.module == "all":
                th_incoming = threading.Thread(target=incoming.main, 
                        args=(modemManager,))

                th_incoming.start()
                th_incoming.join()
                modemManager.daemon()
        except Exception as error:
            logging.exception(error)
