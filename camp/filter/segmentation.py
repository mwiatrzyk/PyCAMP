import logging

from camp.core import Image
from camp.filter import BaseFilter

log = logging.getLogger(__name__)


class Segment(object):
    """Container that holds single extracted segment from image. Objects of
    this class are metioned to be read-only once created."""
    
    def __init__(self, area, edges, color):
        """Create new object.
        
        :param area: set of pixel ``(x,y)`` tuple coordinates
        :param color: color of this object used in image"""
        self.__area = area
        self.__edges = edges
        self.__color = color
    
    @property
    def color(self):
        return self.__color

    @property
    def area(self):
        """Set of pixel coordinates composing this object."""
        return self.__area

    @property
    def edges(self):
        """Set of pixel coordinates that are area pixels adjacent to area
        pixels of different object."""
        return self.__edges

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
    def width(self):
        l, t, r, b = self.bounds
        return r - l

    @property
    def height(self):
        l, t, r, b = self.bounds
        return b - t
    
    @property
    def barycenter(self):
        try:
            return self.__barycenter
        except AttributeError:
            x = sum([a[0] for a in self.area])
            y = sum([a[1] for a in self.area])
            l = float(len(self.area))
            self.__barycenter = x / l, y / l
            return self.__barycenter

    @property
    def coverage(self):
        """Return value representing coverage of bounding rect pixels by
        object's pixels. Returned value ranges from 0 (no object pixels) up to
        1 (all bounding rect's pixels are object's pixels; this means, that
        object is a rectangle)."""
        l, t, r, b = self.bounds
        total = float((r - l + 1) * (b - t + 1))
        return len(self.area) / total
    
    def display(self, image, area_color=None, edge_color=None):
        """Display this object on given image.
        
        :param image: reference to image on which object will be displayed
        :param area_color: color of area pixels of this object
        :param edge_color: color of edge_pixels of this object"""
        if not area_color:
            area_color = (0, 0, 255)
        if not edge_color:
            edge_color = (0, 255, 0)
        p = image.pixels
        for x, y in self.area:
            p[x, y] = area_color
        for edge in self.edges:
            for x, y in edge:
                p[x, y] = edge_color

    def __repr__(self):
        """Return text representation of this object."""
        return "<%s(color=%s, npixels=%d, nedges=%d, bounds=%s)>" %\
            (self.__class__.__name__, self.color, len(self.area), len(self.edges), self.bounds)


class Segmentizer(BaseFilter):
    """Class used to perform segmentation of given image."""

    def process(self, image, storage=None):
        # Neighbourhood generator (coordinates of pixels surrounding given
        # ``(x,y)`` pixel with itself)
        def neighbourhood(x, y):
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
            objects = set()  # Storage for disjoined set of pixel coords
            # While there are pixels to process
            while coords:
                coord = coords.pop()
                area = set([coord])  # Storage for current set of area pixel coords
                edge = set()  # Storage for current set of edge pixel coords (edge < area)
                stack = [coord]  # Recurency stack
                # Pixels are added to stack only if belong to neighbourhood of
                # current pixel
                while stack:
                    p = stack.pop()  # Pop pixel from the stack
                    for n in neighbourhood(p[0], p[1]):  # For each neighbouring pixel
                        if n in coords:  # If not yet processed
                            coords.remove(n)
                            stack.append(n)
                            area.add(n)
                # Extract edge pixels (i.e. area pixels that are adjacent to
                # area pixels of different colors or image edges)
                for a in area:
                    for n in neighbourhood(a[0], a[1]):
                        if n not in area:
                            edge.add(a)
                            break
                # Split set of edge pixels into list of disjoined edge pixels sets
                edges = []
                while edge:
                    coord = edge.pop()
                    tmp = set([coord])
                    stack = [coord]
                    while stack:
                        p = stack.pop()
                        for n in neighbourhood(p[0], p[1]):
                            if n in edge:
                                edge.remove(n)
                                stack.append(n)
                                tmp.add(n)
                    edges.append(tmp)
                objects.add(Segment(area, tuple(edges), color))
            pixels[color] = objects
            log.debug("number of segments extracted for color %s: %d", color, len(objects))
        storage[self.__class__.__name__] = {'segments': pixels}
        return image
