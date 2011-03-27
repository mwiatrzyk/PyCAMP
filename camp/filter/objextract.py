import logging

from camp.core import Image
from camp.filter import BaseFilter

log = logging.getLogger(__name__)


class ExtractedObject(object):
    """Container that holds single extracted from image disjoined object of
    given color. Objects of this class are metioned to be read-only once
    created."""
    
    def __init__(self, area, color):
        """Create new object.
        
        :param area: set of pixel ``(x,y)`` tuple coordinates
        :param color: color of this object used in image"""
        self.__area = area
        self.__color = color
    
    @property
    def area(self):
        """Set of pixel coordinates composing this object."""
        return self.__area

    @property
    def edge(self):
        """Set of border pixel coordinates, i.e. area pixels that are not
        entirely surrounded by another area pixels."""
        print 1

    @property
    def bounds(self):
        """Return bounds of this extracted object as a tuple of ``(x_min,
        y_min, x_max, y_max)``."""
        try:
            return self.__bounds
        except AttributeError:
            xmin = min(self.area, key=lambda x: x[0])
            xmax = max(self.area, key=lambda x: x[0])
            ymin = min(self.area, key=lambda x: x[1])
            ymax = max(self.area, key=lambda x: x[1])
            self.__bounds = xmin[0], ymin[1], xmax[0], ymax[1]
            return self.__bounds

    @property
    def coverage(self):
        """Return value representing coverage of bounding rect pixels by
        object's pixels. Returned value ranges from 0 (no object pixels) up to
        1 (all bounding rect's pixels are object's pixels; this means, that
        object is a rectangle)."""
        l, t, r, b = self.bounds
        total = float((r - l + 1) * (b - t + 1))
        return len(self.area) / total
    
    def display(self, image, color):
        p = image.pixels
        for x, y in self.area:
            p[x, y] = color

    def __repr__(self):
        return "<%s(npixels=%d, bounds=%s)>" %\
            (self.__class__.__name__, len(self.area), self.bounds)


class ObjectExtractor(BaseFilter):
    """Extracts object (disjoined single color areas) from image, possibly
    quantized first."""
    
    def __reduce_noise(self, image, pixels):
        colors = sorted([c for c in image.colors()], key=lambda x: x[0])
        npixels = float(image.width * image.height)
        for o in pixels[colors[0][1]]:
            pass
        return image, pixels

    def process(self, image):
        # Neighbourhood generator (coordinates of pixels surrounding given
        # ``(x,y)`` pixel with itself)
        def neighbourhood(x, y):
            yield x, y
            yield x-1, y    # W
            yield x-1, y-1  # NW
            yield x, y-1    # N
            yield x+1, y-1  # NE
            yield x+1, y    # E
            yield x+1, y+1  # SE
            yield x, y+1    # S
            yield x-1, y+1  # SW
        # Create set of pixel coordinates for each of distinct colors
        pixels = {}
        ptr = image.pixels
        for x in xrange(image.width):
            for y in xrange(image.height):
                pixels.setdefault(ptr[x, y], set()).add((x, y))
        log.debug("number of colors: %d", len(pixels))
        # Walk through each set of pixel coords and split set of coordinates
        # into disjoined sets
        for color, coords in pixels.iteritems():
            objects = []  # Storage for disjoined set of pixel coords
            # While there are pixels to process
            while coords:
                area = set()  # Storage for current set of area pixel coords
                #edge = set()  # Storage for current set of edge pixel coords (edge < area)
                stack = [coords.pop()]
                coords.add(stack[0])  # To avoid KeyError while removing from set
                # Pixels are added to stack only if belong to neighbourhood of
                # current pixel
                while stack:
                    p = stack.pop()  # Pop pixel from the stack
                    for n in neighbourhood(p[0], p[1]):  # For each neighbouring pixel
                        if n in coords:  # If not yet processed
                            coords.remove(n)
                            stack.append(n)
                            area.add(n)
                        #else:
                        #    edge.add(p)
                objects.append(ExtractedObject(area, color))
            pixels[color] = objects
            log.debug("objects extracted for color %s: %d", color, len(objects))
        return self.__reduce_noise(image, pixels)
