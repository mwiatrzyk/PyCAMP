import logging

from camp.core import Image
from camp.filter import BaseFilter

log = logging.getLogger(__name__)


class Classifier(BaseFilter):
    
    def process(self, image, storage=None):
        print image
        return image
