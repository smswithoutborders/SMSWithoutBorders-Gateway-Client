#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import configparser
import logging 
import time
import json
import threading
import base64
import pika

from models.modem import Modem

class NodeInbound(Modem):
    def __init__(self) -> None:
        
        super().__init__()
