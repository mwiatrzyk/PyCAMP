from camp.core import Image
from camp.util import asunicode


class BaseGenre(object):
    """Class that keeps information about segment genre (is it a text, a
    rectangle, a circle or any other object). Concrete genres must inherit from
    this base one."""

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class HybridGenre(BaseGenre):
    """Genre composed with other genres."""

    def __init__(self, **kwargs):
        super(HybridGenre, self).__init__()
        for k, v in kwargs.iteritems():
            if not isinstance(v, BaseGenre):
                raise TypeError(
                    "%s: instance of %s expected, found %s" %
                    (k, BaseGenre, type(v)))
        self._subs = dict(kwargs)
    
    def __iter__(self):
        for k in self._subs:
            yield k

    def __getitem__(self, key):
        return self._subs[key]

    def iteritems(self):
        for k in self:
            yield k, self[k]

    def __repr__(self):
        subreprs = ["%s=%s" % (k, repr(v)) for k, v in self.iteritems()]
        return "%s(%s)" % (
            self.__class__.__name__,
            ', '.join(subreprs))


class FigureGenre(BaseGenre):
    """Base class for figure genre classes."""


class Text(BaseGenre):
    """Genre representing textual regions."""
    
    def __init__(self, text, horizontal=True):
        """Create new Text genre instance.
        
        :param text: text found by OCR software"""
        self.text = asunicode(text)
        self.horizontal = horizontal

    def __repr__(self):
        return "%s(text='%s', horizontal=%s)" %\
            (self.__class__.__name__, self.text, self.horizontal)


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
        self._index = index
        self._color = color
        self._area = set()
        self._border = set()
        self._neighbours = set()
        self._genre = None
    
    @property
    def index(self):
        """Index of this segment."""
        return self._index

    @property
    def color(self):
        """Color of this segment."""
        return self._color

    @property
    def area(self):
        """Set of area pixel coordinates of this segment."""
        return self._area

    @property
    def border(self):
        """Set of border pixel coordinates. This is subset of :param:`area`."""
        return self._border

    @property
    def neighbours(self):
        """Set of adjacent segment indices."""
        return self._neighbours

    @property
    def genre(self):
        """Instance of :class:`BaseGenre` representing genre of this segment."""
        return self._genre
    
    @genre.setter
    def genre(self, value):
        """Genre setter."""
        self._genre = value

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
        """Width of bounding rect of this segment."""
        return self.right - self.left + 1

    @property
    def height(self):
        """Height of bounding rect of this segment."""
        return self.bottom - self.top + 1

    @property
    def barycenter(self):
        """Segment's barycenter coordinates."""
        x = sum([a[0] for a in self.area])
        y = sum([a[1] for a in self.area])
        l = float(len(self.area))
        return x / l, y / l

    @property
    def coverage(self):
        """Bounding rect coverage value in ranging from 0 (no pixels) up to 1
        (entire bounding rect is filled with pixels)."""
        return len(self.area) / float(self.width * self.height)
    
    @property
    def vfactor(self):
        """The bigger the value of this property is, the more 'vertical' is the
        segment."""
        return float(self.height) / float(self.width)

    @property
    def hfactor(self):
        """The bigger the value of this property is, the more 'horizontal' is
        the segment."""
        return float(self.width) / float(self.height)

    def toimage(self, mode='L', color=255, background=0, border=0, angle=None):
        """Convert this segment to image.
        
        :param mode: mode of resulting image
        :param color: color of segment pixels on resulting image
        :param border: image border width (segment pixels will be surrounded by
            border of background color if value is greater than 0)
        :param angle: can be used to create rotated image (usefull for OCR to
            recognize vertical text segments by rotating them to be a
            horizontal text segments)"""
        result = Image.create(mode, self.width + 2 * border, self.height + 2 * border, background=background)
        p = result.pixels
        l, t = self.left, self.top
        for x, y in self.area:
            p[x-l+border, y-t+border] = color
        if angle:
            return result.rotate(angle)
        else:
            return result

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

    def display_barycenter(self, image, color=None):
        """Displays barycenter of this segment on given image.
        
        :param image: reference to image on which barycenter point will be
            placed
        :param color: color of barycenter point"""
        if not color:
            color = (0, 255, 0)
        image.pixels[self.barycenter] = color

    def display_border(self, image, color=None):
        if not color:
            color = (255, 255, 0)
        p = image.pixels
        for x, y in self.border:
            p[x, y] = color

    def __repr__(self):
        """Return text representation of this object."""
        return "<%s(npixels=%d, bounds=%s, genre=%s)>" %\
            (self.__class__.__name__, len(self.area), self.bounds, self.genre)


class SegmentGroup(Segment):
    """Groups two or more segments."""
    
    def __init__(self, index, segments=None):
        """Create new segment group instance.
        
        :param index: index assigned to this segment group"""
        super(SegmentGroup, self).__init__(index=index, color=None)
        self._segments = set(segments or [])
    
    @property
    def segments(self):
        return self._segments

    @property
    def genre(self):
        """Genre of this segment group."""
        return self._genre

    @genre.setter
    def genre(self, value):
        """Genre setter."""
        self._genre = value
        for s in self.segments:
            s.genre = value  # Set genre in underlying segments also

    @property
    def area(self):
        """Area of this segment group (union of all underlying segment
        areas)."""
        return set.union(*[s.area for s in self.segments])

    @property
    def neighbours(self):
        """Neighbours of this segment (union of all underlying segment
        neighbours)."""
        return set.union(*[s.neighbours for s in self.segments])
