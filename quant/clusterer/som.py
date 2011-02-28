import math
import random

from PIL import Image, ImageDraw
from quant.clusterer.metric import euclidean2


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
        self.weight = [self.rnd() for _ in xrange(dim)]


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
        self.rnd = rnd or random.Random().random
        self.nodes = [_Node(dim, i, rnd=self.rnd) for i in xrange(rows*cols)]

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


class RectangularTopology(BaseTopology):

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


class Som(object):
    __som_random__ = random.Random().random
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
        :param rnd: reference to function taking no parameters and returning
            random number of any range (depending on sample vectors' items
            range)
        :param metric: metric function used to calculate difference between two
            vectors of same size. This function should return ``0`` if vectors
            are equal or pisitive number if not. The higher value is, the more
            different vectors are.
        :param topology: instance of :class:`BaseTopology` representing
            topology used by this SOM network"""
        cls = self.__class__
        self.rnd = kwargs.get('rnd') or cls.__som_random__
        self.metric = kwargs.get('metric') or cls.__som_metric__
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
            random.shuffle(samples, random=self.rnd)
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

    def visualize(self):
        def rgb2hsv(rgb):
            rgb = list(rgb)
            for i in xrange(3):
                rgb[i] /= 255.0
            v = max(rgb)
            x = min(rgb)
            if x == v:
                h = s = 0.0
            else:
                if rgb[0] == x:
                    f = rgb[1] - rgb[2]
                    i = 3.0
                elif rgb[1] == x:
                    f = rgb[2] - rgb[0]
                    i = 5.0
                else:
                    f = rgb[0] - rgb[1]
                    i = 1.0
                h = (i - f / (v - x)) * 60.0
                h = h - math.floor(h/359.9) * 359.9 / 359.9   # h mod 359.9
                s = (v - x) / v;
            return h, s, v
        nw, nh = 20, 20
        im = Image.new('RGB', (self.topology.cols * nw, self.topology.rows * nh))
        draw = ImageDraw.Draw(im)
        for n, left, top, right, bottom in self.topology.bounding_boxes(width=nw, height=nh):
            color = (
                int(n.weight[0]), 
                int(n.weight[1]),
                int(n.weight[2]))
            draw.ellipse((left, top, right, bottom), fill=color)
        im.show()
