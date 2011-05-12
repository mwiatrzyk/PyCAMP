"""Core classes & functions."""

from PIL import Image as PILImage, ImageOps, ImageDraw
from PIL import ImageStat as PILImageStat


class Image(object):
    """Proxy class for underlying PIL's Image class."""
    
    def __init__(self, backend):
        self.__backend = backend
    
    def __repr__(self):
        return "<%s(mode=%s, width=%s, height=%s)>" %\
            (self.__class__.__name__, self.mode, self.width, self.height)
    
    ### Read-only properties

    @property
    def backend(self):
        """Get instance of underlying PIL.Image class."""
        return self.__backend

    @property
    def mode(self):
        """Get mode name."""
        return self.backend.mode

    @property
    def bands(self):
        """Return tuple of strings representing each channel (f.e. ``('R', 'G',
        'B')``)."""
        return self.backend.getbands()
    
    @property
    def nchannels(self):
        """Return number of channels in the image."""
        return len(self.bands)

    @property
    def width(self):
        """Get image width in pixels."""
        return self.backend.size[0]

    @property
    def height(self):
        """Get image height in pixels."""
        return self.backend.size[1]
    
    @property
    def size(self):
        """Return ``(width, height)`` tuple for this image."""
        return self.backend.size

    @property
    def npixels(self):
        """Return number of pixels in image."""
        return self.width * self.height

    @property
    def pixels(self):
        """Return PIL object that provides fast access to image pixels. Pixel
        can be accessed on resulting object by getting ``(x,y)`` key on it."""
        return self.backend.load()

    @property
    def draw(self):
        """Return reference to PIL's ImageDraw class intance allowing to draw
        on current image."""
        return ImageDraw.Draw(self.backend)

    ### Public methods
    
    def colors(self, encoder=None):
        """Return list of ``(amount, color)`` tuples each representing number
        of occurences of ``color`` in the image. The result of this method can
        be used as color historgram.
        
        :param encoder: function that takes color tuple as the argument and
            returns converted color (maybe to other colorspace)"""
        if not encoder:
            for c in self.backend.getcolors(self.width * self.height):
                yield c
        else:
            for n, c in self.backend.getcolors(self.width * self.height):
                yield n, encoder(c)
    
    def convert(self, mode, matrix=None):
        """Convert this image to different mode and return converted image.
        
        :param mode: mode string
        :param matrix: optional conversion matrix"""
        return Image(self.backend.convert(mode, matrix))
    
    def paste(self, image, left=0, top=0):
        """Paste another image into this image. This function affects current
        image (i.e. does not create a new one).
        
        :param image: reference to image that will be pasted
        :param left: coordinate of ``image`` left edge in this image's
            coordinates
        :param top: coordinates of ``image`` top edge in this image's 
            coordinates"""
        if not isinstance(image, Image):
            raise TypeError("image: expecting instance of Image, found %s" % type(image))
        self.backend.paste(image.backend, (left, top))
        return self
    
    def filter(self, filter_):
        """Filter image with given filter and returned filtered image.
        
        :param filter_: PIL filter"""
        return Image(self.backend.filter(filter_))

    def rotate(self, angle):
        return Image(self.backend.rotate(angle))

    def colormask(self, colors):
        """Create mask that masks given set of colors in the image."""
        colors = set(colors)
        dest = Image.create('1', self.width, self.height)
        sp, dp = self.pixels, dest.pixels
        for x in xrange(self.width):
            for y in xrange(self.height):
                if sp[x, y] in colors:
                    dp[x, y] = 1
                else:
                    dp[x, y] = 0
        return dest

    def save(self, filename):
        """Save current image in given file.
        
        :param filename: path to image file"""
        return self.backend.save(filename)
    
    ### Pickle support

    def __getstate__(self):
        return {
            'mode': self.mode,
            'size': self.backend.size,
            'data': self.backend.tostring()}

    def __setstate__(self, state):
        self.__backend = PILImage.fromstring(
            state['mode'], state['size'], state['data'])

    ### Constructors
    
    @classmethod
    def create(cls, mode, width, height, background=None):
        """Create image of given mode and size and return new instance of Image
        class.
        
        :param mode: name of mode (i.e. RGB)
        :param width: desired image width
        :param height: desired image height
        :param background: background color"""
        image = Image(PILImage.new(mode, (width, height)))
        if background:
            draw = image.draw
            draw.rectangle((0, 0, image.width-1, image.height-1), fill=background)
        return image

    @classmethod
    def load(cls, filename):
        """Load image from given file and return instance of Image class.
        
        :param filename: path to image file"""
        return Image(PILImage.open(filename))


class ImageStat(object):
    """Statistical information of given image."""
    
    def __init__(self, image):
        """Create new instance of ImageStat class.
        
        :param image: reference to Image class object"""
        if not isinstance(image, Image):
            raise TypeError("image: expecting instance of %s, found %s" % (Image, type(image)))
        self.__stat = PILImageStat.Stat(image.backend)
        self.__image = image

    @property
    def extrema(self):
        return self.__stat.extrema

    @property
    def mean(self):
        return self.__stat.mean

    @property
    def median(self):
        return self.__stat.median

    @property
    def var(self):
        return self.__stat.var

    @property
    def stddev(self):
        return self.__stat.stddev

    @property
    def ncolors(self):
        return len([c for c in self.__image.colors()])

    def __repr__(self):
        return "<%s(ncolors=%s)>" %\
            (self.__class__.__name__, self.ncolors)
