import logging

from hashlib import md5
from camp.core import Image
from camp.filter.quantization import Quantizer
from camp.filter.segmentation import Segmentizer
from camp.filter.objrecognize import ObjectRecognitor
from camp.filter.featuredetection import ImageFeatureDetector

log = logging.getLogger(__name__)


class Application(object):
    
    def run(self, source, dest, **options):
        # Calculate md5 checksum of a file (used by caching utility)
        key = md5(open(source).read()).hexdigest()

        # Load source image
        source = Image.load(source).convert('RGB')

        # Create filter stack
        f = None
        f = ObjectRecognitor(next_filter=f)
        f = Segmentizer(next_filter=f)
        #f = ImageFeatureDetector(next_filter=f)
        f = Quantizer(next_filter=f, colorspace='LAB', threshold2=3)

        # Execute filter stack
        f(source, storage={}, key=key).save(dest)
