import math
import random


class Random(random.Random):
    """Overrides standard Random class and allows to specify range for the
    ``uniform`` function."""
    
    def __init__(self, rmin=0, rmax=1, seed=None):
        """Create new instance of random number generator.
        
        :param rmin: minimal value of random numbers generated by the
            ``uniform`` function
        :param rmax: maximal value of random numbers generated by the
            ``uniform`` function"""
        super(Random, self).__init__(seed)
        self.rmin = rmin
        self.rmax = rmax

    def uniform(self):
        """Generate random number from range specified in constructor."""
        return super(Random, self).uniform(self.rmin, self.rmax)


class Vector(object):
    """Class representing n-dimensional vectors."""
    
    def __init__(self, items):
        """Create new vector.
        
        :param items: sequence of vector's items"""
        self._items = tuple(items)

    def length(self):
        """Calculate length of this vector."""
        return math.sqrt(sum([c**2 for c in self]))

    def normalize(self):
        """Return a vector that is normalized version of current one."""
        l = self.length()
        return Vector([c/l for c in self])

    def dot(self, other):
        """Calculate dot product of this vector and provided another vector."""
        if len(self) != len(other):
            raise TypeError("vectors must have same dimensions")
        return sum([self[i]*other[i] for i in xrange(len(self))])
    
    def __mul__(self, other):
        """Allows to calculate dot product with * operator."""
        if not isinstance(other, Vector):
            raise TypeError(
                "unsupported operand type(s) for *: %s and %s" %
                (type(self), type(other)))
        return self.dot(other)

    def __iter__(self):
        for i in self._items:
            yield i

    def __getitem__(self, key):
        return self._items[key]

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return "%s([%s])" % (
            self.__class__.__name__,
            ', '.join([str(i) for i in self]))

    @classmethod
    def new(cls, a, b):
        """Make new vector pointing from ``a`` towards ``b`` and return new
        vector."""
        if len(a) != len(b):
            raise TypeError("points must have same dimensions")
        return Vector([b[i]-a[i] for i in xrange(len(a))])


def asbool(value):
    """Convert given value to boolean True or False."""
    if isinstance(value, bool):
        return value
    if value in ('True', 'true', 'Yes', 'yes', 1):
        return True
    if value in ('False', 'false', 'No', 'no', 0):
        return False
    return bool(value)
