import logging

from camp.filter import BaseFilter

log = logging.getLogger(__name__)


class ObjectRecognitor(BaseFilter):
    
    def process(self, data):
        image, objects = data
        print [c for c in image.colors()]
        print sum([len(o.area) for o in objects[(0,0,0)]])
        for color, tmp in objects.iteritems():
            print color, len(tmp), sum([len(o.area) for o in tmp])
        return image
