from camp.util import Vector
from camp.clusterer.metric import euclidean
from camp.core.containers import FigureGenre
from camp.plugins.recognition import RecognitorPluginBase


class RectangleGenre(FigureGenre):
    pass


class RectangleRecognitor(RecognitorPluginBase):
    
    def test(self, segment):
        # FIXME: this is simplified version of rectangle recognition algorithm
        corners = self.extract_corners(segment)
        if len(corners) != 4:
            return 0
        corners = set(corners)
        # Order corners by nearest neighbour (choose and remove first and then
        # choose and remove nearest one making it new first)
        c = [corners.pop()]
        while corners:
            tmp = min(corners, key=lambda x: euclidean(x, c[-1]))
            corners.remove(tmp)
            c.append(tmp)
        # Check if segment c[0]-c[1] is parallel to segment c[2]-c[3]. Do this
        # by checking dot product
        a1 = Vector.new(c[0], c[1]).normalize()
        a2 = Vector.new(c[2], c[3]).normalize()
        if abs(a1*a2) != 1:
            return 0
        # Check if segment c[1]-c[2] is parallel to segment c[3]-c[0]
        b1 = Vector.new(c[1], c[2]).normalize()
        b2 = Vector.new(c[3], c[0]).normalize()
        if abs(b1*b2) != 1:
            return 0
        # Now check if adjacent segments are perpendicular. If so, a rectangle
        # is found
        if not abs(a1*b1) and not abs(a1*b2) and not abs(a2*b1) and not abs(a2*b2):
            return 1
        else:
            return 0
