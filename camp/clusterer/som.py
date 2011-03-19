import math
import random

from PIL import Image, ImageDraw
from camp.util import Random
from camp.clusterer.metric import euclidean2


class _Node(object):
    """Container class representing single SOM node."""

    def __init__(self, dim, index, rnd):
        """Create new SOM node.
        
        :param dim: size of weight vector
        :param index: index of this node from the beginning of SOM nodes
            array 
        :param rnd: random number generator function"""
        self.index = index
        self.rnd = rnd
        self.weight = [self.rnd[i].uniform() for i in xrange(dim)]


class BaseTopology(object):
    
    def __init__(self, rows, cols, dim, rnd=None):
        """Create new topology.
        
        :param rows: number of SOM grid rows
        :param cols: number of SOM grid columns
        :param dim: dimension of single sample (size of vector)
        :param rnd: random number generator function (will be used
            ``Random.random`` if ommited)"""
        self.rows = rows
        self.cols = cols
        self.rnd = rnd or Random()
        self.nodes = [_Node(dim, i, rnd=self.rnd) for i in xrange(rows*cols)]
        try:
            self.initialize()
        except NotImplementedError:
            pass
    
    def __getitem__(self, key):
        return self.nodes[key[0] * self.cols + key[1]]

    def neighbourhood(self, bmu, radius):
        """Generator of ``(index, distance)`` tuples, each containing ``index``
        of neighbouring node and ``distance`` (measured according to
        neighbourhood used) from best matching unit (BMU).
        
        :param bmu: index of best matching unit
        :param radius: radius of neighbourhood that will be generated"""
        raise NotImplementedError()

    def bounding_boxes(self, width=20, height=20):
        """Generator of neighbourhood's nodes bounding boxes. This method is
        used to visualize SOM grid. Each generated value is a 5 element tuple
        of following format: ``(n, left, top, right, bottom)``, where ``n`` is
        reference to current node, ``left`` and ``top`` are coordinates of
        node's bounding box upper left corner and ``right`` and ``bottom`` are
        coordinates of node's bounding box bottom right corner.
        
        :param width: bounding box width
        :param height: bounding box height"""
        raise NotImplementedError()

    def initialize(self):
        raise NotImplementedError()


class RectangularTopology(BaseTopology):
    """Implementation of rectangular topology."""

    def neighbourhood(self, bmu, radius):
        cols = self.cols
        rows = self.rows
        row = bmu / cols
        col = bmu % cols
        radius = int(radius)
        rowstart = row-radius
        if rowstart < 0:
            rowstart = 0
        rowend = row+radius
        if rowend >= rows:
            rowend = rows-1
        colstart = col-radius
        if colstart < 0:
            colstart = 0
        colend = col + radius
        if colend >= cols:
            colend = cols-1
        for r in xrange(rowstart, rowend+1):
            for c in xrange(colstart, colend+1):
                yield r * cols + c, max(abs(r-row), abs(c-col))

    def bounding_boxes(self, width=20, height=20):
        for n in self.nodes:
            x = n.index % self.cols
            y = n.index / self.cols
            left = x * width + 1
            top = y * height + 1
            right = left + width - 1
            bottom = top + height - 1
            yield n, left, top, right, bottom

    def _initialize(self):
        self[0,0].weight = [1.0, 0.0, 0.0]
        self[0,self.cols-1].weight = [0.0, 1.0, 0.0]
        self[self.rows-1, 0].weight = [0.0, 0.0, 1.0]
        for r in xrange(self.rows):
            for c in xrange(self.cols):
                self[r, c].weight = [0,0,0]#[c/float(self.cols), r/float(self.rows), c/float(self.cols)]


class Som(object):
    __som_random__ = None
    __som_metric__ = staticmethod(euclidean2)
    __som_topology__ = RectangularTopology
    __som_radius_modifier__ = 2.0
    __som_learning_rate__ = 0.5

    def __init__(self, rows, cols, dim, **kwargs):
        """Create new SOM network.
        
        :param rows: number of SOM grid rows
        :param cols: number of SOM grid cols
        :param dim: dimension of vectors in training set

        Following optional arguments can also be given:
        :param rnd: list of random number generator instances. Each instance
            must be subclass of ``random.Random`` class. Length of list must be
            exactly ``dim``.
        :param metric: metric function used to calculate difference between two
            vectors of same size. This function should return ``0`` if vectors
            are equal or pisitive number if not. The higher value is, the more
            different vectors are.
        :param topology: instance of :class:`BaseTopology` representing
            topology used by this SOM network"""
        cls = self.__class__
        self.rnd = kwargs.get('rnd') or cls.__som_random__
        if not isinstance(self.rnd, list):
            raise TypeError("rnd: expecting list, not %s" % type(self.rnd))
        for i, r in enumerate(self.rnd):
            if not isinstance(r, random.Random):
                raise TypeError("rnd[%d]: expecting %s, found %s" % (i, random.Random, type(r)))
        self.metric = kwargs.get('metric') or cls.__som_metric__
        if not callable(self.metric):
            raise TypeError("metric: callable expected")
        self.topology = (kwargs.get('topology') or cls.__som_topology__)(
            rows, cols, dim, self.rnd)
        self.radius_modifier = kwargs.get('radius_modifier') or cls.__som_radius_modifier__
        self.learning_rate = kwargs.get('learning_rate') or cls.__som_learning_rate__
    
    ### Special methods

    def __repr__(self):
        return "<%s(rows=%d, cols=%d, dim=%d)>" %\
            (self.__class__.__name__, 
            self.topology.rows, 
            self.topology.cols, 
            self.topology.dim)

    ### Public methods

    def train(self, samples, epochs):
        """Evaluates training procedure by presenting vectors from ``samples``
        array to SOM network.
        
        :param samples: sequence of training vectors. Each vectors must have
            same size, matching :param:`dim` of constructor."""
        max_radius = max(self.topology.rows, self.topology.cols)/2
        for e in xrange(epochs):
            # Shuffle samples (change order)
            random.shuffle(samples, random=self.rnd[0].random)
            # For each sample in sample sequence
            for sample in samples:
                # Perform best match unit (BMU) search. This step needs to compare
                # current sample with all nodes of SOM grid
                bmu = self.bmu(sample)
                # Calculate current neighbourhood radius (radius decreases
                # during learning process)
                radius = max_radius * math.exp(-e/(epochs/math.log(self.radius_modifier*max_radius)))
                # Calculate current learning factor (learning factor decreases
                # during learning process)
                learning_rate = self.learning_rate * math.exp(-e/(epochs/4.0))
                # BMU is found - let's start weight modification
                for index, distance in self.topology.neighbourhood(bmu.index, 1):
                    # Scale learning rate by distance from BMU
                    factor = learning_rate * math.exp(-(distance**2)/float(radius**2))
                    # Modify weights 
                    w = self.topology.nodes[index].weight
                    for i in xrange(len(w)):
                        w[i] += factor * (sample[i]-w[i])
    
    def bmu(self, sample):
        """Find and return best matching unit (BMU) node instance for given
        ``sample`` vector.
        
        :param sample: sample vector"""
        bmu = self.topology.nodes[0]
        val = self.metric(sample, bmu.weight)
        for node in self.topology.nodes[1:]:
            tmp = self.metric(sample, node.weight)
            if tmp < val:
                bmu = node
                val = tmp
        return bmu

    def visualize(self, width=20, height=20, scale=255, convert=None):
        """Uses PIL library to create and return Image representing actual
        state of this SOM network.
        
        :param width: width of single bounding box
        :param height: height of single bounding box"""
        im = Image.new('RGB', (self.topology.cols * width, self.topology.rows * height))
        draw = ImageDraw.Draw(im)
        for n, left, top, right, bottom in self.topology.bounding_boxes(width=width, height=height):
            tmp = convert(n.weight) if convert else tuple(n.weight)
            color = (
                int(tmp[0] * scale),
                int(tmp[1] * scale),
                int(tmp[2] * scale))
            draw.ellipse((left, top, right, bottom), fill=color)
        return im
