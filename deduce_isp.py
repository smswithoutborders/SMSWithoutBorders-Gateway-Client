#!/bin/python

import re
import os
import configparser

CONFIGS = configparser.ConfigParser(interpolation=None)
ISP_CONFIGS = configparser.ConfigParser(interpolation=None)
OPERATORS_CONFIGS = configparser.ConfigParser(interpolation=None)

PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
ISP_PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'isp_configs', "isp.ini")
ISP_PATH_CONFIG_FILE_DEFAULT = os.path.join(os.path.dirname(__file__), 'isp_configs', "default.ini")
OPERATORS_PATH_CONFIG_FILE_DEFAULT = os.path.join(os.path.dirname(__file__), 'isp_configs', "operators.ini")

if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
    exit()
if os.path.exists( ISP_PATH_CONFIG_FILE ):
    ISP_CONFIGS.read(ISP_PATH_CONFIG_FILE)
elif os.path.exists( ISP_PATH_CONFIG_FILE_DEFAULT ):
    if os.path.exists( OPERATORS_PATH_CONFIG_FILE_DEFAULT ):
        OPERATORS_CONFIGS.read( OPERATORS_PATH_CONFIG_FILE_DEFAULT)
    print(">> ISP comes from default.ini")
    ISP_CONFIGS.read(ISP_PATH_CONFIG_FILE_DEFAULT)
else:
    raise Exception(f"ISP config file not found: {ISP_PATH_CONFIG_FILE}")
    exit()

def rm_country_code(phonenumber):
    country_code = ISP_CONFIGS[CONFIGS["ISP"]["country"]]["..country_code"]
    if country_code[0] == "+":
        country_code = '\\' + country_code
    if re.search(str('^' + country_code), phonenumber):
        return phonenumber[(len(country_code)-1):]
    else:
        return phonenumber


def acquire_isp(operator_code):
    country = CONFIGS["ISP"]["country"]
    OPERATORS_PATH_CONFIG_FILE_DEFAULT = os.path.join(os.path.dirname(__file__), 'isp_configs', "operators.ini")
    OPERATORS_CONFIGS.read( OPERATORS_PATH_CONFIG_FILE_DEFAULT)
    
    for isp in OPERATORS_CONFIGS[country]:
        if OPERATORS_CONFIGS[country][isp] == operator_code:
            return isp

    return None


def deduce_isp(phonenumber):
    country = CONFIGS["ISP"]["country"]
    region_isp = ISP_CONFIGS[country]
    for isp in region_isp:
        if isp == "..country_code":
            continue

        rgexs = region_isp[isp].split(',')
        for rgex in rgexs:
            if re.search(rgex, phonenumber):
                return isp
    
    return None

if __name__ == "__main__":
    MTN="6521"
    ORANGE="6921"
    NEXTTELL="6621"

    phonenumber = "+237652156"
    phonenumber=rm_country_code(phonenumber)
    isp = deduce_isp(phonenumber)
    assert(phonenumber=="652156")
    assert(isp == "mtn")
