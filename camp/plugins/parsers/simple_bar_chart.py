import logging

from lxml import etree

from camp.util import asfloat
from camp.core.containers import SegmentGroup
from camp.plugins.parsers import ParserPluginBase, ParsingResultBase
from camp.plugins.recognitors.rectangle import RectangleGenre

log = logging.getLogger(__name__)


class VerticalBar(SegmentGroup):
    """Groups vertical rectangle with its text description."""
    
    def __init__(self, bar, label):
        super(VerticalBar, self).__init__(None, segments=[bar, label])
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
    
    def __init__(self, bars, argument_domain=None, value_domain=None, title=None):
        super(SimpleBarChartResult, self).__init__()
        self.bars = bars
        self.argument_domain = argument_domain or ''
        self.value_domain = value_domain or ''
        self.title = title or ''

    def tostring(self):
        attributes = etree.SubElement(self.content, 'Attributes')
        # Title of chart
        etree.SubElement(attributes, 'Title').text = self.title
        # Argument domain
        arg_domain = etree.SubElement(attributes, 'Domain')
        arg_domain.attrib['Of'] = 'Arg'
        arg_domain.text = self.argument_domain
        # Value domain
        val_domain = etree.SubElement(attributes, 'Domain')
        val_domain.attrib['Of'] = 'Value'
        val_domain.text = self.value_domain
        # Bars
        bars = etree.SubElement(attributes, 'Bars')
        for b in sorted(self.bars, key=lambda x: x.left):
            etree.SubElement(bars, 'Bar').\
            attrib.update({
                'Arg': b.label.genre.text.strip(),
                'Value': "%1.3f" % (b.value if b.value is not None else b.bar.height)})
        return super(SimpleBarChartResult, self).tostring()


class SimpleBarChartParser(ParserPluginBase):
    
    def __init__(self, *args, **kwargs):
        super(SimpleBarChartParser, self).__init__(*args, **kwargs)
        # Map of text.barycenter -> text
        self.text_by_barycenter = dict([(t.barycenter, t) for t in self.text])
        # Set of text barycenters (performance gain)
        self.text_barycenters = set(self.text_by_barycenter.keys())
        # List of all rectangles
        self.rectangles = [
            s for s in self.simple_figures
            if isinstance(s.genre, RectangleGenre)]
        # Map of rectangle.bounds -> rectangle
        self.rect_by_bounds = dict([(r.bounds, r) for r in self.rectangles])
        # Set of rectangle bounds (performance gain)
        self.rect_bounds = set(self.rect_by_bounds.keys())

    def __extract_vertical_bars(self):
        """Extract, create and return list of :class:`VerticalBar` instances
        representing vertical bars of simple bar chart."""
        bars = []
        # Sort rectangles by decreasing coordinate of rectanle bottom
        rect_by_bounds_sorted = sorted(
            self.rect_by_bounds.iterkeys(), key=lambda x: -x[3])
        # Iterate via rectangle bounds starting from lying bottom-most
        for k in rect_by_bounds_sorted:
            # Search for label candidates for current rectangle. Label
            # candidates are text regions whth horizontal centers lying just
            # below the rectangle (but not too far)
            label_candidates = filter(
                lambda x: x[0]>k[0] and x[0]<k[2] and x[1]>k[3] and x[1]-k[3]<=50,
                self.text_barycenters)
            if not label_candidates:
                continue
            # Use nearest label candidate as bar label
            label = min(label_candidates, key=lambda x: x[1])
            # Create vertical bar segment and add it to list of vertical bars found
            bar = VerticalBar(
                bar=self.rect_by_bounds[k],
                label=self.text_by_barycenter[label])
            bars.append(bar)
            # Make label not to be usable by another bars
            self.text_barycenters.remove(label)
        return bars

    def __determine_height2value_factor(self, bars):
        """Determine factor used to calculate bar value by multiplying
        resulting factor by bar height. If factor is undeterminable this
        function returns 1 (bar height in pixels is numerically equal to real
        bar value)."""
        # Leave only that text areas that are on the left side of leftmost bar
        leftmost_bar = min(bars, key=lambda x: x.left)
        left = leftmost_bar.left
        bottom = leftmost_bar.bottom
        leftmost_text = filter(lambda x: x[0]<left and x[1]<bottom+10, self.text_barycenters)
        # If text area could not be found, return neutral factor (1)
        if not leftmost_text:
            return 1.0
        scale = []
        # Calculate average Y position where all bars starts
        startpoint = int(sum([b.bar.bottom for b in bars]) / float(len(bars)))
        # Find in previously created `leftmost_text` sequence the region that
        # is closest to leftmost bar
        t = max(leftmost_text, key=lambda x: x[0]+x[1])
        # Find all text areas lying in vertical column formed by `t`. Sort it
        # in decreasing order of `bottom` position as well
        remaining = sorted(
            filter(lambda x: t[0]>x.left and t[0]<x.right and x.top<t[1], self.text),
            key=lambda x: -x.bottom)
        # Try to convert text to float
        for r in remaining:
            try:
                # Try to convert text to float number
                tmp = asfloat(r.genre.text)
                # If there is `0` in the Y axis values use its barycenter as
                # startpoint for more accurate results
                if tmp == 0.0:
                    startpoint = r.barycenter[1]
                if not tmp:
                    continue
                # Add parsed value and its pixel height to list of results
                scale.append((
                    asfloat(r.genre.text),
                    abs(r.barycenter[1]-startpoint)))
            except ValueError, e:
                log.warning(e)
                continue
        # Maybe parsing was not successfull
        if not scale:
            return 1.0
        # Calculate single factor by averaging scales
        value = sum([s[0] for s in scale]) / float(len(scale))
        height = sum([s[1] for s in scale]) / float(len(scale))
        return value / height
    
    def parse(self):
        # Extract all vertical bars
        bars = self.__extract_vertical_bars()
        if not bars:
            return
        # Assign values to bars (if not yet assigned)
        if filter(lambda x: x.value is None, bars):
            factor = self.__determine_height2value_factor(bars)
            if factor:
                for b in bars:
                    if b.value is None:
                        b.value = b.bar.height * factor
        # Return results
        return SimpleBarChartResult(bars)
