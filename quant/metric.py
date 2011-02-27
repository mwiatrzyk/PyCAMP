"""Definition of metric functions. Each metric function takes two arguments:
sequences representing two vectors of same dimensions. Metric functions are
used to measure similarity of given vectors (distance from one to another). The
lower return value is, the more similar vectors are."""


def euclidean2(a, b):
    """Calculates squared Euclidean distance between given two vectors."""
    return sum([(a[i]-b[i])**2 for i in xrange(len(a))])
