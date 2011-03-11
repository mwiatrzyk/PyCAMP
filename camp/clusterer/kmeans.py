import random

from camp.util import Random
from camp.clusterer.metric import euclidean2


class Cluster(object):
    """Class representing k-means clusters. Each cluster have its own centroid
    and set of samples, that might be empty. Instances of this class are used
    to initialize :func:`kmeans` function.
    
    :attr __c_metric__: metric function to be used (may be overriden in
        constructor)
    :attr __c_rnd__: random number generator(-s) instance(-s)
    
    Instances of this class will also have following public properties
    available:

    :param rnd: for details see :attr:`__c_rnd__`
    :param metric: for details see :attr:`__c_metric__`
    :param samples: set of samples assigned to this cluster
    :param centroid: centroid of this cluster"""
    __c_metric__ = staticmethod(euclidean2)
    __c_rnd__ = Random(rmin=0, rmax=255)

    def __init__(self, dim, metric=None, rnd=None):
        """Create new cluster.
        
        :param dim: dimension of centroid vector
        :param metric: metric used to calculate distance between centroid and
            sample
        :param rnd: list of ``random.Random`` instances or single
            ``random.Random`` instance used to randomize centroid key"""
        self.dim = dim
        self.rnd = rnd or self.__class__.__c_rnd__
        if isinstance(self.rnd, list):
            if len(self.rnd) != dim:
                raise ValueError("rnd: expecting exactly %d elements in list" % dim)
            for i, r in enumerate(self.rnd):
                if not isinstance(r, random.Random):
                    raise TypeError("rnd[%d]: expecting random.Random instance, found %s" % (i, type(r)))
        elif isinstance(self.rnd, random.Random):
            self.rnd = [self.rnd for _ in xrange(dim)]
        else:
            raise TypeError("rnd: expecting random.Random instance or list of random.Random instances, found %s" % (i, type(r)))
        self.metric = metric or self.__class__.__c_metric__
        self._acc = [0 for i in xrange(dim)]  # Accumulator of sumarized samples
        self.samples = set()
        self.centroid = tuple(
            [self.rnd[i].uniform() for i in xrange(dim)])

    def distance(self, sample):
        """Calculate distance between centroid of this cluster and given sample
        using provided metric function (euclidean by default).
        
        :param sample: single sample from training set"""
        return self.metric(self.centroid, sample)

    def add(self, sample):
        """Add sample vector to this cluster.
        
        :param sample: single sample from training set"""
        acc = self._acc
        for i in xrange(self.dim):
            acc[i] += sample[i]
        self.samples.add(sample)

    def update(self):
        """Update cluster by calculating new centroid and clearing set of
        assigned samples and accumulator."""
        if not self.samples:
            return  # Do nothing if cluster does not have any samples assigned
        total = float(len(self.samples))
        acc = self._acc
        acc = [acc[i]/total for i in xrange(self.dim)]
        self._acc = [0 for i in xrange(self.dim)]
        self.samples = set()
        self.centroid = tuple(acc)

    def __repr__(self):
        """Return string representation of cluster."""
        return "<%s(centroid=%s, samples=%d)>" %\
            (self.__class__.__name__, self.centroid, len(self.samples))


def kmeans(samples, clusters, max_epochs=10):
    """Split samples into k-clusters using provided initial list of
    clusters.
    
    :param samples: array of sample vectors having same size
    :param clusters: array containing k-clusters
    :param max_epochs: specifies maximal number of training epochs. One
        training epoch is exactly one iteration over ``clusters`` array"""
    if not isinstance(clusters, list) or len(clusters) == 0:
        raise TypeError("clusters: list of Cluster instances expected, found %s" % type(clusters))
    dim = clusters[0].dim
    for i, c in enumerate(clusters[1:]):
        if c.dim != dim:
            raise ValueError("clusters[%d]: dimensions differ: %d != %d" % (i+1, c.dim, dim))
    for epoch in xrange(max_epochs):
        # Assign each sample to the nearest cluster
        for sample in samples:
            min(clusters, key=lambda x: x.distance(sample)).add(sample)
        # Termination check
        if epoch == max_epochs - 1:
            return clusters
        # Reorganize cluster centroids by averaging assigned samples
        for c in clusters:
            c.update()
