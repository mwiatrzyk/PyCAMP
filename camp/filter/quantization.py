import logging

from camp.core import Image, ImageStat
from camp.core.colorspace import Convert
from camp.util import Random
from camp.filter import BaseFilter
from camp.convert import rgb2hsv, hsv2rgb
from camp.clusterer.metric import euclidean
from camp.clusterer.kmeans import kmeans, Cluster

log = logging.getLogger(__name__)


class Quantizer(BaseFilter):
    __q_colorspace__ = 'LAB'
    __q_threshold1__ = 0.1
    __q_threshold2__ = 5.0

    def __init__(self, next_filter=None, colorspace=None, threshold1=None, threshold2=None):
        super(Quantizer, self).\
            __init__(next_filter=next_filter)
        self.colorspace = colorspace.lower() if colorspace else\
            self.__class__.__q_colorspace__.lower()
        self.__c_encoder = getattr(Convert, "rgb2%s" % self.colorspace)\
            if self.colorspace != 'rgb' else lambda x: x
        self.__c_decoder = getattr(Convert, "%s2rgb" % self.colorspace)\
            if self.colorspace != 'rgb' else lambda x: x
        self.threshold1 = threshold1 or self.__class__.__q_threshold1__
        self.threshold2 = threshold2 or self.__class__.__q_threshold2__

    def __get_samples(self, image):
        """Prepare and return list of samples for clusterer."""
        if image.mode != 'RGB':
            raise ValueError("image: expecting RGB image, found %s" % image.mode)
        return [s[1] for s in image.colors(encoder=self.__c_encoder)]

    def __create_result_image(self, image, clusters):
        """Create result image by changing color of each pixel in source image
        to one of cluster centroid colors."""
        encoder = self.__c_encoder
        decoder = self.__c_decoder
        res = Image.create(image.mode, image.width, image.height)
        dpix = res.pixels
        spix = image.pixels
        cache = {}
        for y in xrange(image.height):
            for x in xrange(image.width):
                s = spix[x, y]
                if s not in cache:
                    for c in clusters:
                        if encoder(s) in c.samples:
                            val = decoder(c.centroid)
                            break
                    cache[s] = val
                    dpix[x, y] = val
                else:
                    dpix[x, y] = cache[s]
        return res

    def choose_clusters(self, image):
        """Heuristic used to choose cluster centers from training set.
        
        :param image: image to be quantized"""
        t1 = self.threshold1
        t2 = self.threshold2
        clusters = []
        npixels = float(image.npixels)
        metric = euclidean
        dim = image.nchannels
        max_difference = metric(
            self.__c_encoder((0, 0, 0)),
            self.__c_encoder((255, 255, 255)))
        # Sort colors by number of occurences in the image, descending and
        # ignore rare colors
        colors = sorted([c for c in image.colors(encoder=self.__c_encoder) if c[0]/npixels*100 >= t1], key=lambda x: -x[0])
        for i in xrange(len(colors)):
            if not colors[i]:
                continue  # Go to next color - already processed
            candidates = []
            # Search for colors that are close to current color
            for j in xrange(len(colors)):
                if not colors[j]:
                    continue  # Go to next color - already processed
                diff = metric(colors[i][1], colors[j][1]) / max_difference * 100
                if diff <= t2:
                    candidates.append(colors[j][1])
                    if j != i:
                        colors[j] = None  # Mark color as processed
            # Calculate centroid
            centroid = [0, 0, 0]
            ncandidates = float(len(candidates))
            for k in xrange(len(centroid)):
                centroid[k] = sum([c[k] for c in candidates]) / ncandidates
            colors[i] = None  # Mark color as processed
            # Add new cluster
            clusters.append(Cluster(dim, metric=metric, centroid=tuple(centroid)))
        return clusters
    
    def process(self, image):
        if not isinstance(image, Image):
            raise TypeError("image: expecting %s, found %s" % (Image, type(image)))
        # Get samples from the source image
        samples = self.__get_samples(image)
        log.debug("number of color before quantization: %d", len(samples))
        # Choose initial clusters for the K-Means clusterer
        initial_clusters = self.choose_clusters(image)
        log.debug("number of clusters found: %d", len(initial_clusters))
        # Perform clustering and return clusters
        clusters = kmeans(samples, initial_clusters)
        # Create output image
        return self.__create_result_image(image, clusters)

class QuadTreeNode(object):

    def __init__(self, left, top, size, parent=None):
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None
        self.left = left
        self.top = top
        self.size = size
        self.parent = parent
        self.pixels = {}

    def __repr__(self):
        return "<%s(left=%d, top=%d, size=%d)>" %\
            (self.__class__.__name__, self.left, self.top, self.size)


class QuadTreeSplitter(BaseFilter):
    
    def __build_quadtree(self, image, src_left, src_top, src_right, src_bottom):
        draw = image.draw
        pixels = image.pixels
        def proxy(parent):
            left, top, size = parent.left, parent.top, parent.size
            cx = left + size / 2
            cy = top + size / 2
            if left+size < src_left or left > src_right:
                return
            if top+size < src_top or top > src_bottom:
                return
            if size > 2:
                parent.nw = QuadTreeNode(left, top, size/2, parent=parent)
                proxy(parent.nw)
                parent.ne = QuadTreeNode(cx, top, size/2, parent=parent)
                proxy(parent.ne)
                parent.sw = QuadTreeNode(left, cy, size/2, parent=parent)
                proxy(parent.sw)
                parent.se = QuadTreeNode(cx, cy, size/2, parent=parent)
                proxy(parent.se)
            else:
                for i in xrange(size):
                    for j in xrange(size):
                        parent.pixels[left+i, top+j] = pixels[left+i, top+j]
        tree = QuadTreeNode(0, 0, image.width)
        proxy(tree)
        return tree

    def __merge_quadtree(self, root):
        ptr = root
        while ptr.nw:
            ptr = ptr.nw
        print ptr

    def process(self, image):
        background = max(image.colors(), key=lambda x: x[0])[1]
        powers = [2**n for n in xrange(32)]
        min_size = max(image.width, image.height)
        for size in powers:
            if size > min_size:
                break
        src_left = (size - image.width) / 2
        src_top = (size - image.height) / 2
        wrapped = Image.create(image.mode, size, size, background=background)
        wrapped.paste(image, src_left, src_top)
        root = self.__build_quadtree(wrapped, src_left, src_top, src_left+image.width-1, src_top+image.height-1)
        self.__merge_quadtree(root)
        return wrapped
