import weakref
import logging

from camp.core import Image
from camp.core.containers import Segment, SegmentSet
from camp.filter import BaseFilter

log = logging.getLogger(__name__)


def neighbourhood(x, y):
    yield x-1, y    # W
    yield x-1, y-1  # NW
    yield x, y-1    # N
    yield x+1, y-1  # NE
    yield x+1, y    # E
    yield x+1, y+1  # SE
    yield x, y+1    # S
    yield x-1, y+1  # SW


def neighbourhood_with_bound_check(x, y, w, h):
    if x > 0:
        yield x-1, y    # W
        if y > 0:
            yield x-1, y-1  # NW
        if y < h-1:
            yield x-1, y+1  # SW
    if x < w-1:
        if y > 0:
            yield x+1, y-1  # NE
        yield x+1, y    # E
        if y < h-1:
            yield x+1, y+1  # SE
    if y < h-1:
        yield x, y+1    # S
    if y > 0:
        yield x, y-1    # N


class Segmentizer(BaseFilter):
    """Class used to perform segmentation of given image. The output of this
    class is following:
        * list of all segments
        * matrix NxN of connections between segments"""
    __f_enable_caching__ = True
    
    def __create_coordinate_sets(self, image):
        """Create map of ``color->pixel_coord_set`` for all pixels composing
        given image. Results of this method are later used by
        :meth:`__get_segments`."""
        log.debug('creating set of pixel coordinates for each color')
        pixels = {}
        ptr = image.pixels
        for x in xrange(image.width):
            for y in xrange(image.height):
                pixels.setdefault(ptr[x, y], set()).add((x, y))
        return pixels

    def __get_segments(self, pixels):
        """Create list of all disjoint segments by splitting sets of pixel
        coordinates for each color into disjoint subsets. Results of this
        method are later used to create connection matrix."""
        # Neighbourhood generator (coordinates of pixels surrounding given
        # ``(x,y)`` pixel with itself)
        log.debug('extracting segments from image')
        segments = []
        for color, coords in pixels.iteritems():
            while coords:
                coord = coords.pop()
                stack = [coord]
                # Create new segment
                segment = Segment(index=len(segments), color=color)
                segment.area.add(coord)
                # Pixels are added to stack only if belong to neighbourhood of
                # current pixel
                while stack:
                    p = stack.pop()  # Pop pixel from the stack
                    for n in neighbourhood(p[0], p[1]):  # For each neighbouring pixel
                        if n in coords:  # If not yet processed
                            coords.remove(n)
                            stack.append(n)
                            segment.area.add(n)
                # Once stack is empty, new segment is extracted and should be
                # added to the list of extracted segments
                segments.append(segment)
        return segments

    def __label_pixels(self, segments, image):
        """Assign each pixel to its segment and return assignment map having
        same size as the image (map[x,y] stores index of segment from
        ``segments`` list to which current pixel belongs)."""
        log.debug('labelling pixels in the image')
        pixel_map = [[None for _ in xrange(image.height)] for _ in xrange(image.width)]
        for s in segments:
            for x, y in s.area:
                pixel_map[x][y] = s.index
        return pixel_map

    def __get_neighbours(self, segments, pixel_map, image):
        """Fill ``neighbours`` property of each segment with weakrefs to
        neighbouring segments. This method will create undirected graph of
        segments."""
        log.debug('creating list of neighbouring segments for each segment')
        #nseg = len(segments)
        sorted_segments = sorted(segments, key=lambda x: x.index)
        #print sorted_segments[0].index, sorted_segments[1].index
        #matrix = [[None for _ in xrange(nseg)] for _ in xrange(nseg)]
        for x in xrange(image.width):
            for y in xrange(image.height):
                label = pixel_map[x][y]
                for nx, ny in neighbourhood_with_bound_check(x, y, image.width, image.height):
                    this_label = pixel_map[nx][ny]
                    if label != this_label:
                        sorted_segments[label].neighbours.add(this_label)
                        sorted_segments[this_label].neighbours.add(label)
                        #matrix[label][this_label] = matrix[this_label][label] = True
        #for i in xrange(nseg):
        #    for j in xrange(nseg):
        #        if matrix[i][j]:
        #            #segments[i].neighbours.append(weakref.ref(segments[j]))
        #            segments[i].neighbours.add(segments[j])
        #            segments[j].neighbours.add(segments[i])
        return segments

    def process(self, image, storage=None):
        log.info('performing segmentation step')
        # Create set of pixel coordinates for each color giving map of (color,
        # set_of_coords)
        pixels = self.__create_coordinate_sets(image)
        # Create list of segments by splitting all sets of pixel coordinates
        # into disjoint subsets
        segments = self.__get_segments(pixels)
        # Label pixels in the image
        pixel_map = self.__label_pixels(segments, image)
        # Create connection matrix using previously labelled pixel map
        segments = self.__get_neighbours(segments, pixel_map, image)
        log.debug("total number of segments extracted: %d", len(segments))
        storage[self.__class__.__name__] = {'segments': SegmentSet(segments)}
        return image
