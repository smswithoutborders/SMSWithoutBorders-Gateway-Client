#!/usr/bin/env python3


import os
import sys
import logging
import threading

import node
import gateway
from common.CustomConfigParser.customconfigparser import CustomConfigParser


if __name__ == "__main__":
    getattr(logging, loglevel.upper())
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        # raise ValueError('Invalid log level: %s' % loglevel)
        number_level = logging.INFO

    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    logging.basicConfig(
            format='%(asctime)s|[%(levelname)s] %(pathname)s %(lineno)d|%(message)s',
            # datefmt='%Y-%m-%d %I:%M:%S %p',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler('src/services/logs/service.log'),
                logging.StreamHandler(sys.stdout) ],
            encoding='utf-8',
            level=numeric_level)

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
        if sys.argv[1] == "--node":
            node_thread = threading.Thread(target=node.main, 
                    args=(config, config_event_rules, config_isp_default, config_isp_operators,),
                    daemon=True)


            logging.info("starting node thread")
            node_thread.start()
            logging.info("node thread started")
            node_thread.join()

        elif sys.argv[1] == "--gateway":
            gateway_thread = threading.Thread(target=gateway.main, 
                    args=(config, config_event_rules, config_isp_default, config_isp_operators,),
                    daemon=True)

            logging.info("starting gateway thread")
            gateway_thread.start()
            logging.info("gateway thread started")
            gateway_thread.join()
    except Exception as error:
        logging.error(error)
