"""Definition of metric functions. Each metric function takes two arguments:
sequences representing two vectors of same dimensions. Metric functions are
used to measure similarity of given vectors (distance from one to another). The
lower return value is, the more similar vectors are."""
import math


def euclidean2(a, b):
    """Calculates squared Euclidean distance between given two vectors."""
    return sum([(a[i]-b[i])**2 for i in xrange(len(a))])


def euclidean(a, b):
    """Calculates euclidean distance between two vectors."""
    return math.sqrt(euclidean2(a, b))


def hsvmetric(a, b):
    """Calculates distance between given two HSV colors."""
    def deg2rad(x):
        return math.pi * 2.0 * x / 360.0
    def hue2val(h):
        return (1.0 - (math.cos(deg2rad(h)) + 1.0) / 2.0)
    def threshold(v):
        return 1.0 - 0.8*v
    h1, s1, v1 = a[0], a[1]/100.0, a[2]/100.0
    p = (0, hue2val(h1)) if s1 > threshold(v1) else (1, v1)
    h2, s2, v2 = b[0], b[1]/100.0, b[2]/100.0
    q = (0, hue2val(h2)) if s2 > threshold(v2) else (1, v2)
    #if p[0] == q[0]:
    #    return abs(p[1]-q[1])
    #else:
    return euclidean((hue2val(h1), s1, v1), (hue2val(h2), s2, v2))
