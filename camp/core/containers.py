from camp.core import Image


class SegmentGenre(object):
    pass


class Text(SegmentGenre):
    
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "%s(text='%s')" % (self.__class__.__name__, self.text)


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
        self.genre = None

    @property
    def bounds(self):
        """Return bounds of this extracted object as a tuple of ``(left, top,
        right, bottom)``."""
        if not self.area:
            return
        return self.left, self.top, self.right, self.bottom
    
    @property
    def left(self):
        """X coordinate of top left hand corner."""
        return min(self.area or [(-1, -1)], key=lambda x: x[0])[0]

    @property
    def top(self):
        """Y coordinate of top left hand corner."""
        return min(self.area or [(-1, -1)], key=lambda x: x[1])[1]

    @property
    def right(self):
        """X coordinate of bottom right hand corner."""
        return max(self.area or [(-1, -1)], key=lambda x: x[0])[0]

    @property
    def bottom(self):
        """Y coordinate of bottom right hand corner."""
        return max(self.area or [(-1, -1)], key=lambda x: x[1])[1]

    @property
    def width(self):
        return self.right - self.left + 1

    @property
    def height(self):
        return self.bottom - self.top + 1

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
    
    def toimage(self, mode='RGB', color=(255, 255, 255), border=0, rotate=None):
        result = Image.create(mode, self.width + 2 * border, self.height + 2 * border)
        p = result.pixels
        l, t = self.left, self.top
        for x, y in self.area:
            p[x-l+border, y-t+border] = color
        return result.rotate(rotate) if rotate else result

    def display(self, image, color=None, ):
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

    def display_barycenter(self, image, color=None):
        """Displays barycenter of this segment on given image.
        
        :param image: reference to image on which barycenter point will be
            placed
        :param color: color of barycenter point"""
        if not color:
            color = (0, 255, 0)
        image.pixels[self.barycenter] = color

    def __repr__(self):
        """Return text representation of this object."""
        return "<%s(npixels=%d, bounds=%s)>" %\
            (self.__class__.__name__, len(self.area), self.bounds)


class SegmentGroup(Segment):
    
    def __init__(self, index):
        self.index = index
        self.segments = set()
        self._genre = None

    @property
    def genre(self):
        return self._genre

    @genre.setter
    def genre(self, value):
        self._genre = value
        for s in self.segments:
            s.genre = value

    @property
    def area(self):
        return set.union(*[s.area for s in self.segments])

    @property
    def neighbours(self):
        return set.union(*[s.neighbours for s in self.segments])
