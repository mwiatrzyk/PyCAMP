import logging

from camp.util import asfloat
from camp.core.containers import SegmentGroup
from camp.plugins.parsers import ParserPluginBase, ParsingResultBase
from camp.plugins.recognitors.rectangle import RectangleGenre

log = logging.getLogger(__name__)


class VerticalBar(SegmentGroup):
    
    def __init__(self, index, bar, label):
        super(VerticalBar, self).__init__(index, segments=[bar, label])
        self._bar = bar
        self._label = label
        self.value = None

    @property
    def bar(self):
        return self._bar

    @property
    def label(self):
        return self._label


class SimpleBarChartResult(ParsingResultBase):
    __pr_input_type__ = u'SIMPLE_BAR_CHART'
    
    def __init__(self, bars, x_label=None, y_label=None, title=None):
        self.bars = bars
        self.x_label = x_label
        self.y_label = y_label
        self.title = title

    def tostring(self):
        result = super(SimpleBarChartResult, self).tostring()
        result = u"%s\n\nNumber of bars: %d" % (result, len(self.bars))
        result = u"%s\n\nBars (from left to right):" % result
        for b in sorted(self.bars, key=lambda x: x.left):
            result = u"%s\n\t%s = %s" % (result, b.label.genre.text, b.value or b.height)
        return result


class SimpleBarChartParser(ParserPluginBase):
    
    def parse(self):
        text_by_centroid = dict([(t.barycenter, t) for t in self.text])
        text_centroids = set(text_by_centroid.keys())

        rectangles = [s for s in self.simple_figures if isinstance(s.genre, RectangleGenre)]
        rect_by_bounds = dict([(r.bounds, r) for r in rectangles])
        rect_bounds = set(rect_by_bounds.keys())
        
        # Extract vertical bars with accompanying labels
        bars = []
        for index, k in enumerate(sorted(rect_by_bounds.iterkeys(), key=lambda x: -x[3])):
            matching = filter(lambda x: x[0]>k[0] and x[0]<k[2] and x[1]>k[3] and x[1]-k[3]<=50, text_centroids)
            if not matching:
                continue
            label = min(matching, key=lambda x: x[1])
            bar = VerticalBar(index, bar=rect_by_bounds[k], label=text_by_centroid[label])
            bars.append(bar)
            text_centroids.remove(label)
        if not bars:
            return  # Not a bar chart

        # Guess scale of chart
        scale = []
        leftmost_bar = min(bars, key=lambda x: x.left)
        left = leftmost_bar.left
        leftmost_text = filter(lambda x: x[0]<left, text_centroids)
        startpoint = int(sum([b.bar.bottom for b in bars]) / float(len(bars)))
        if leftmost_text: 
            t = max(leftmost_text, key=lambda x: x[0]+x[1])
            remaining = filter(lambda x: t[0]>x.left and t[0]<x.right, self.text)
            for r in remaining:
                try:
                    tmp = asfloat(r.genre.text)
                    if not tmp:
                        continue
                    scale.append((
                        asfloat(r.genre.text),
                        abs(r.barycenter[1]-startpoint)))
                except ValueError, e:
                    log.warning(e)
                    continue
        
        # Scale is not determinable - only pixel height can be used
        if not scale:
            return SimpleBarChartParser(bars)

        # Estimate bar values
        avg_scale = sum([s[0] for s in scale]) / float(len(scale)),\
                    sum([s[1] for s in scale]) / float(len(scale))
        for b in bars:
            b.value = (b.height * avg_scale[0]) / avg_scale[1]

        return SimpleBarChartResult(bars)
