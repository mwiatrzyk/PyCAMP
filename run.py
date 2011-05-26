#!/usr/bin/python2.6

import os
import sys
import logging

from optparse import OptionParser

from camp.app import Application
from camp.config import Config

Config.ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

parser = OptionParser(usage='Usage: %prog [options] [input] [output]')
parser.add_option('-c', '--config', dest='config',
    help='path to config file to be used. If this option is not given, '
    'configuration from "./doc/config_default.ini" will be used',
    metavar='PATH')
parser.add_option('-t', '--timeit', dest='timeit',
    help='enable timer to measure execution time (works only in verbose mode)',
    default=False, action='store_true')
parser.add_option('-d', '--dump', dest='dump', 
    help='enable partial results dumping', default=False, action='store_true')
parser.add_option('-v', '--verbose', dest='verbose',
    help='enable verbose mode', default=False, action='store_true')
parser.add_option('', '--cbounds', dest='cbounds',
    help='color to be used for segment bounds when creating dumps '
    'of partial results')

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(0)
options, args = parser.parse_args()
if len(args) == 0:
    parser.error('input and output file paths are missing')
elif len(args) == 1:
    parser.error('output file path is missing')

logging.basicConfig(
    level=logging.DEBUG if options.verbose else logging.INFO,
    format='%(levelname).1s: [%(name)s] %(message)s')

try:
    logging.info('PyCAMP is starting')
    status = Application(args[0], args[1], options=options).run()
    logging.info('PyCAMP is finishing with status code %d', status)
    sys.exit(status)
except Exception:
    logging.exception('an error occured:')
    sys.exit(1)
