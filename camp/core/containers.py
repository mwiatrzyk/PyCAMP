
class Segment(object):
    """Container that holds single extracted segment from image. Each segment
    instance has following public properties (with read and write access):
    
    :param index: unique index of this segment
    :param color: original color of pixels listed in :param:`area`
    :param area: set of ``(x,y)`` tuples of pixel coordinates
    :parma neighbours: set of indices of segments adjacent to current one"""
    
    def __init__(self, index, color):
        """Create new segment.
        
        :param index: unique integer index of this segment. Indices are used to
            provide neighbourhood relationship between segments
        :param color: color of this object used in image"""
        self.index = index
        self.color = color
        self.area = set()
        self.neighbours = set()

    @property
    def bounds(self):
        """Return bounds of this extracted object as a tuple of ``(x_min,
        y_min, x_max, y_max)``."""
        if not self.area:
            return
        xmin = min(self.area, key=lambda x: x[0])
        xmax = max(self.area, key=lambda x: x[0])
        ymin = min(self.area, key=lambda x: x[1])
        ymax = max(self.area, key=lambda x: x[1])
        return xmin[0], ymin[1], xmax[0], ymax[1]

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
        x = sum([a[0] for a in self.area])
        y = sum([a[1] for a in self.area])
        l = float(len(self.area))
        return x / l, y / l

    @property
    def coverage(self):
        """Return value representing coverage of bounding rect pixels by
        object's pixels. Returned value ranges from 0 (no object pixels) up to
        1 (all bounding rect's pixels are object's pixels; this means, that
        object is a rectangle)."""
        l, t, r, b = self.bounds
        total = float((r - l + 1) * (b - t + 1))
        return len(self.area) / total
    
    def display(self, image, color=None):
        """Display this object on given image.
        
        :param image: reference to image on which object will be displayed
        :param area_color: color of area pixels of this object
        :param edge_color: color of edge_pixels of this object"""
        if not color:
            color = (0, 0, 255)
        p = image.pixels
        for x, y in self.area:
            p[x, y] = color

    def display_bounds(self, image, color=None):
        """Display bounds of this segment on given image.
        
        :param image: reference to image on which bounds will be displayed
        :param color: color of bound rectangle"""
        if not color:
            color = (255, 0, 0)
        image.draw.rectangle(self.bounds, outline=color)

    def __repr__(self):
        """Return text representation of this object."""
        return "<%s(color=%s, npixels=%d, bounds=%s)>" %\
            (self.__class__.__name__, self.color, len(self.area), self.bounds)


class SegmentSet(set):
    
    def merge(self, s1, s2):
        """Merge two segments in segment set by joining segment with lower area
        with segment with higher area. Segment with lower area is removed from
        the set. This method returns new set of segments.
        
        :param s1: first segment
        :param s2: second segment"""
        if s1 not in self or s2 not in self:
            raise KeyError("both s1 and s2 segments must exist in set")
        result = SegmentSet(self)
        if len(s1.area) >= len(s2.area):
            major, minor = s1, s2
        else:
            major, minor = s2, s1
        # Join areas and set of neighbours
        major.area.union(minor.area)
        major.neighbours.union(minor.neighbours)
        # If major segment is a neighbour to minor segment remove such
        # neighbourhood
        if minor in major.neighbours:
            major.neighbours.remove(minor)
        # Clean set of neighbours of segments neighbouring with current minor
        # segment and also add major segment as neighbour
        for n in minor.neighbours:
            n.neighbours.remove(minor)
            n.neighbours.add(major)
        result.remove(minor)
        return result


