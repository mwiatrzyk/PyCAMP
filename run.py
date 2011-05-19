#!/usr/bin/python2.6

import sys
import logging

from optparse import OptionParser

from camp.app import Application

parser = OptionParser(usage='Usage: %prog [options] [input] [output]')
parser.add_option('-c', '--config', dest='config',
    help='path to config file to be used instead the default one',
    metavar='PATH')
parser.add_option('-v', '--verbose', dest='verbose', 
    help='enable verbose mode', default=False, action='store_true')

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
    status = Application.instance(options.config).run(*args)
    sys.exit(status)
except Exception:
    logging.exception('an error occured:')
    sys.exit(1)
