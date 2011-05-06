#!/usr/bin/python2.6

import sys
import logging

from camp.app import Application

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

sys.exit(Application().run(*sys.argv[1:]))
