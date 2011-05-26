import os
import logging
import ConfigParser

from hashlib import md5
from camp.util import timeit
from camp.core import Image
from camp.config import Config
from camp.filters.quantization import Quantizer
from camp.filters.segmentation import Segmentizer
from camp.filters.figurerecognition import FigureRecognitor
from camp.filters.textrecognition import TextRecognitor
from camp.filters.parsing import Parser

log = logging.getLogger(__name__)


def _decode_color(color):
    """Decode command line color to tuple that can be used in PIL's
    functions."""
    if not color:
        return
    try:
        return tuple([int(ch) for ch in color.split('.')])
    except ValueError:
        log.warning("expected color format is 'r.g.b', where r, g and b are "
            "integer numbers")


class Application(object):
    """The bootstrap class."""
    
    def __init__(self, infile, outfile, options=None):
        """Create new instance of Application class.
        
        :param infile: input file path
        :param outfile: output file path
        :param options: options instance returned by OptionParser's
            ``parse_args`` method"""
        super(Application, self).__init__()
        if not infile:
            raise ValueError('infile: value is missing')
        if not outfile:
            raise ValueError('outfile: value is missing')
        self.infile = infile
        self.outfile = outfile
        if options:
            argv = {
                'infile': infile,  # Input file path
                'outfile': outfile,  # Output file path
                'timeit': options.timeit,  # Enable or disable `timeit` decorator
                'dump': options.dump,  # Enable or disable `dump` decorator
                'cbounds': _decode_color(options.cbounds)
            }
            Config.instance(config=options.config, argv=argv)

    @timeit
    def run(self):
        """Execute application and return exit code."""
        # Load source image
        source = Image.load(self.infile)
        if source.mode != 'RGB':
            source = source.convert('RGB')
        
        # Create filter stack
        f = None
        f = Parser(next_filter=f)
        f = FigureRecognitor(next_filter=f)
        f = TextRecognitor(next_filter=f)
        f = Segmentizer(next_filter=f)
        f = Quantizer(next_filter=f)

        # Execute filter stack
        f(source, storage={}, key=source.checksum()).save(self.outfile)

        return 0
