import math
import logging

from camp.filter import BaseFilter
from camp.core import Image
from camp.core.colorspace import Convert

log = logging.getLogger(__name__)


def distance(a, b):
    #return math.sqrt((b[0]-a[0])**2 + (b[1]-a[1])**2)
    return abs(b[0]-a[0]) + abs(b[1]-a[1])

def right(a, b):
    dist = b[0] - a[0]
    if dist < 0:
        return 2**32
    return dist + abs(b[1]-a[1])


class ObjectRecognitor(BaseFilter):
    
    def __find_background(self, image, objects):
        """Return set of *background* objects. An object is said to be the
        *background* object if it bounds (at least one) are simultaneously
        image bounds."""
        result = set()
        for color, objs in objects.iteritems():
            left = min(objs, key=lambda x: x.bounds[0])
            if left.bounds[0] == 0:
                result.add(left)
            right = max(objs, key=lambda x: x.bounds[2])
            if right.bounds[2] == image.width-1:
                result.add(right)
            top = min(objs, key=lambda x: x.bounds[1])
            if top.bounds[1] == 0:
                result.add(top)
            bottom = max(objs, key=lambda x: x.bounds[3])
            if bottom.bounds[3] == image.height-1:
                result.add(bottom)
        return result


    def process(self, data):
        image, objects = data
        background = self.__find_background(*data)
        maxc = max([c for c in image.colors()], key=lambda x: x[0])
        max_distance = distance((0, 0), (image.width-1, image.height-1)) #math.sqrt(image.width**2 + image.height**2)
        '''color = (0, 0, 0)
        tmp = set(objects[color])
        starting = min(tmp, key=lambda x: x.bounds[0]*x.bounds[1])
        tmp.remove(starting)
        i = 0
        while tmp:
            #starting.display(image)
            next_ = min(tmp, key=lambda x: right(starting.barycenter, x.barycenter))
            #print next_.barycenter
            tmp.remove(next_)
            starting = next_
            i += 1
            if i >= 50:
                break
        #starting.display(image)
        #next_.display(image)
        for i, a in enumerate(objects[color]):
            continue
            b = min(objects[color], key=lambda x: distance(x.barycenter, a.barycenter) if x is not a else max_distance)
            if i < 1:
                continue
            a.display(image)
            b.display(image)
            return image'''
        for color in objects:
            print color, Convert.rgb2hsv(color), sum([len(o.area) for o in objects[color]]) / float(image.width*image.height) * 100
        image = Image.create(image.mode, image.width, image.height)
        for o in background:
            o.display(image)
        return image
