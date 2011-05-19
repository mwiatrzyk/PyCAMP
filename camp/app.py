import os
import logging
import ConfigParser

from hashlib import md5
from camp.util import timeit
from camp.core import Image
from camp.config import Config
from camp.filter.quantization import Quantizer
from camp.filter.segmentation import Segmentizer
from camp.filter.objrecognize import ObjectRecognitor
from camp.filter.parsing import Parser

log = logging.getLogger(__name__)


class Application(object):
    __instance = None
    
    def __init__(self, config=None):
        """Create new instance of Application class.
        
        :param config: name of config file to be used instead of default one"""
        super(Application, self).__init__()
        Config.instance(config=config)

    @classmethod
    def instance(cls, config=None):
        """Create a singleton instance of Application class.
        
        :param config: optional path to config file"""
        if not cls.__instance:
            cls.__instance = Application(config=config)
        return cls.__instance
    
    @timeit
    def run(self, source, dest, **options):
        """Execute application and return exit code.
        
        :param source: source image file path
        :param dest: destination data file path"""
        config = Config.instance()

        # Load source image
        source = Image.load(source).convert('RGB')
        
        # Create filter stack
        f = None
        f = Parser(next_filter=f)
        f = ObjectRecognitor(next_filter=f)
        f = Segmentizer(next_filter=f)
        f = Quantizer(next_filter=f)

        # Execute filter stack
        f(source, storage={}, key=source.checksum()).save(dest)
