#!/bin/python

import re
import os
import configparser

CONFIGS = configparser.ConfigParser(interpolation=None)
ISP_CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
    exit()

ISP_PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'isp_configs', "isp.ini")
if os.path.exists( ISP_PATH_CONFIG_FILE ):
    ISP_CONFIGS.read(ISP_PATH_CONFIG_FILE)
else:
    raise Exception(f"ISP config file not found: {ISP_PATH_CONFIG_FILE}")
    exit()


def deduce_isp(phonenumber):
    region_isp = ISP_CONFIGS[CONFIGS["ISP"]["country"]]
    for isp in region_isp:
        if isp == "..country_code":
            continue

        rgexs = region_isp[isp].split(',')
        for rgex in rgexs:
            if re.search(rgex, phonenumber):
                print(">>Found match")
                return isp
    
    return None

if __name__ == "__main__":
    MTN="6521"
    ORANGE="6921"
    NEXTTELL="6621"

    isp = deduce_isp("652156")
    print(isp)
