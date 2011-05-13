#!/usr/bin/python2.6

import sys
import logging

from camp.app import Application

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    status = Application.instance('config.ini').run(*sys.argv[1:])
    sys.exit(status)
except Exception:
    logging.exception('an error occured:')
    sys.exit(1)
