import os

from camp.core.containers import FigureGenre


class RecognitorPluginBase(object):
    """Base class for simple geometrical figures recognition plugins. Simple
    means that entire figure is enclosed in one segment.
    
    :attr __rp_priority__: priority value of plugin used to sort list of
        plugins by priorities in ascending order (lower values - higher
        priority)"""
    __rp_priority__ = 0

    def extract_feature_points_by_mask(self, segment, mask, area=False):
        """Extract all feature points for given ``segment`` that match given
        9-element tuple ``mask``.
        
        :param segment: segment for which feature points will be extracted
        :param mask: 9-element tuple mask containing zeros and ones"""
        if len(mask) != 9:
            raise ValueError("mask: expecting 9 element sequence")
        def neighbourhood(x, y):
            yield mask[0], x-1, y-1  # NW
            yield mask[1], x, y-1    # N
            yield mask[2], x+1, y-1  # NE
            yield mask[3], x-1, y    # W
            yield mask[5], x+1, y    # E
            yield mask[6], x-1, y+1  # SW
            yield mask[7], x, y+1    # S
            yield mask[8], x+1, y+1  # SE
        result = []
        set_of_data = segment.area if area else segment.border
        for x, y in set_of_data:
            for state, nx, ny in neighbourhood(x, y):
                test = (nx, ny) in set_of_data
                if bool(state) != test:
                    break
            else:
                result.append((x, y))
        return result
    
    def extract_corners(self, segment):
        """Extracts corner feature points of given segment.
        
        :param segment: segment to be processed"""
        masks = [
            # upper left corner
            (0, 0, 0,
             0, 1, 1,
             0, 1, 0),
            # upper right corner
            (0, 0, 0,
             1, 1, 0,
             0, 1, 0),
            # bottom left corner
            (0, 1, 0,
             0, 1, 1,
             0, 0, 0),
            # bottom right corner
            (0, 1, 0,
             1, 1, 0,
             0, 0, 0)]
        result = []
        for m in masks:
            result.extend(self.extract_feature_points_by_mask(segment, m))
        return result

    def test(self, segment):
        """Test if segment ``segment`` is geometrical figure recognized by this
        class and return value in range 0 (absolutely something different) up
        to 1 (ideal figure).
        
        :param segment: currently being processed segment
        :param remaining: set of remaining segments, can be used to search for
            other parts of ``segment`` - usage depends on concrete class. This
            set can be freely modified by the method
        :param processed: initialized with empty set. Used to mark segments
            taken from ``remaining`` as already processed
        :param groups: initialized with empty set. Should be filled with
            :class:`SegmentGroup` instances if recognition process is creating
            groups.
        :rtype: float"""
        raise NotImplementedError()

    @classmethod
    def load_all(cls):
        """Load all available figure recognition plugins and return as list of
        ``(GenreClass, RecognitorClass)`` tuples sorted by
        :attr:`__rp_priority__`."""
        result = []
        for entry in os.listdir(os.path.join(*tuple(__name__.split('.')))):
            if entry.startswith('_'):
                continue
            if not entry.endswith('.py'):
                continue
            prefix = ''.join([n.title() for n in entry[:-3].split('_')])
            genre_classname = "%sGenre" % prefix
            recognitor_classname = "%sRecognitor" % prefix
            module = __import__(
                "%s.%s" % (__name__, entry[:-3]),
                fromlist=[genre_classname, recognitor_classname])
            GenreClass = getattr(module, genre_classname)
            if not issubclass(GenreClass, FigureGenre):
                raise TypeError(
                    "%s from module %s: expecting subclass of %s" %
                    (GenreClass, module, FigureGenre))
            RecognitorClass = getattr(module, recognitor_classname)
            if not issubclass(RecognitorClass, RecognitorPluginBase):
                raise TypeError(
                    "%s from module %s: expecting subclass of %s" %
                    (RecognitorClass, module, RecognitorPluginBase))
            result.append((GenreClass, RecognitorClass))
        return sorted(result, key=lambda x: x[1].__rp_priority__)


# TODO: complex plugins (such as recognition of arrows) are not yet done
class ComplexRecognitorPluginBase(RecognitorPluginBase):
    """Base class for classes performing recognition of complex figures, i.e.
    figures not entirely enclosed in one segment."""

    @classmethod
    def load_all(cls):
        """Load all complex figures recognition plugins and return list of
        ``(GenreClass, RecognitorClass)`` tuples."""
        result = []
        for GenreClass, RecognitorClass in super(ComplexRecognitorPluginBase, cls).load_all():
            if issubclass(RecognitorClass, ComplexRecognitorPluginBase):
                result.append((GenreClass, RecognitorClass))
        return result
