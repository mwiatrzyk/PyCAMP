import logging

from camp.core import Image, ImageStat
from camp.util import Random
from camp.filter import BaseFilter
from camp.convert import rgb2hsv, hsv2rgb
from camp.clusterer.metric import euclidean
from camp.clusterer.kmeans import kmeans, Cluster

log = logging.getLogger(__name__)


class QuantizationFilter(BaseFilter):
    
    def choose_clusters(self, image):
        """Heuristic used to choose cluster centers from training set.
        
        :param image: image to be quantized"""
        clusters = []
        npixels = float(image.npixels)
        metric = euclidean
        dim = image.nchannels
        max_difference = metric((0, 0, 0), (255, 255, 255))
        # Sort colors by number of occurences in the image, descending and
        # ignore rare colors
        colors = sorted([c for c in image.colors() if c[0]/npixels*100 >= 0.1], key=lambda x: -x[0])
        for i in xrange(len(colors)):
            if not colors[i]:
                continue  # Go to next color - already processed
            candidates = []
            # Search for colors that are close to current color
            for j in xrange(len(colors)):
                if not colors[j]:
                    continue  # Go to next color - already processed
                diff = metric(colors[i][1], colors[j][1]) / max_difference * 100
                if diff < 8.0:
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
        if image.mode != 'RGB':
            raise ValueError("image: expecting RGB image, found %s" % image.mode)
        log.debug("number of color before quantization: %d", ImageStat(image).ncolors)
        clusters = kmeans([s[1] for s in image.colors()], self.choose_clusters(image))
        res = Image.create(image.mode, image.width, image.height)
        dpix = res.pixels
        spix = image.pixels
        cache = {}
        for y in xrange(image.height):
            for x in xrange(image.width):
                s = spix[x, y]
                if s not in cache:
                    for c in clusters:
                        if s in c.samples:
                            val = c.centroid
                            break
                    cache[s] = val
                    dpix[x, y] = val
                else:
                    dpix[x, y] = cache[s]
        log.debug("number of colors after quantization: %d", ImageStat(res).ncolors)
        return res


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
