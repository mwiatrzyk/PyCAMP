import random


class Node(object):
    """Class representing single SOM network node."""

    def __init__(self, dim, offset, rnd=None):
        """Create new SOM node.
        
        :param dim: size of weight vector
        :param offset: offset of this node from the beginning of SOM nodes
            array 
        :param rnd: optional instance of random number generator (new is
            created if ommited)"""
        self.__offset = offset
        self.__random = rnd or random.Random()
        self.__weight = [self.__random.random() for _ in xrange(dim)]

    def __repr__(self):
        return str(self.__weight)

    ### Read only properties

    @property
    def offset(self):
        return self.__offset

    @property
    def weight(self):
        return self.__weight

    ### Public functions

    def metric(self, v):
        """Apply metric function to weight vector and given vector, returning
        result of metric function.
        
        :param v: vector of same dimension as weight vector to be compared with
            it by using metric function"""
        w = self.__weight
        return sum([(w[i]-v[i])**2 for i in xrange(len(v))])

    def update(self, v):
        """Update weight vector of current node.
        
        :param v: current sample
        :param epoch: number of current training epoch
        :param bmu_dist: distance of this node to current BMU node"""
        w = self.__weight
        for i in xrange(len(w)):
            w[i] += v[i] - w[i]


class Som(object):
    
    def __init__(self, rows, cols, dim, rnd=None):
        """Create new SOM network.
        
        :param rows: number of SOM grid rows
        :param cols: number of SOM grid cols
        :param dim: dimension of vectors in training set
        :param rnd: optional Random instance to be used as random number
            generator by this SOM network"""
        self.__rows = rows
        self.__cols = cols
        self.__dim = dim
        self.__random = rnd or random.Random()
        self.__nodes = [Node(dim, i, rnd=self.__random) for i in xrange(rows*cols)]
    
    ### Read only properties

    @property
    def rows(self):
        return self.__rows

    @property
    def cols(self):
        return self.__cols

    @property
    def dim(self):
        return self.__dim

    @property
    def nodes(self):
        return self.__nodes
    
    ### Public methods

    def neighbourhood(self, index, radius):
        """Index generator of neighbouring nodes to node at ``index``.
        
        :param index: index of central node
        :param radius: radius of neighbourhood that will be returned. If radius
            is ``0``, only ``index`` must be returned"""

    def train(self, samples, epochs=None):
        """Evaluates training procedure by presenting vectors from ``samples``
        array to SOM network.
        
        :param samples: sequence of training vectors. Each vectors must have
            same size, matching :param:`dim` of constructor."""
        # Shuffle samples (change order)
        random.shuffle(samples, random=self.__random.random)
        # For each sample in sample sequence
        for sample in samples:
            # Perform best match unit (BMU) search. This step needs to compare
            # current sample with all nodes of SOM grid
            bmu = None
            val = self.__nodes[0].metric(sample)
            for node in self.__nodes[1:]:
                nval = node.metric(sample)
                if nval < val:
                    bmu = node
                    val = nval
            # BMU is found - let's start weight modification



if __name__ == '__main__':
    net = Som(8, 8, 3)
    samples = [
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [0, 1, 1],
        [1, 1, 0],
        [1, 1, 1],
        [0, 0, 0]]
    net.train(samples)
    print net.nodes
    print random.Random().random()
