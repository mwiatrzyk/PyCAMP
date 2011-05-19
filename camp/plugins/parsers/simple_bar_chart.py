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
    """Plugin used to parse simple bar charts - a bar charts with vertical
    bars, with both axis signed and with title.
    
    :attr __p_extract_vertical_bars_t1__: used while searching for chart bars.
        If distance (along Y axis) between rectangle's "bottom" and text
        region's "barycenter" is less or equal given threshold, rectangle is
        said to be a chart bar and text region is said to be bar's label. This
        threshold is used only against text regions that has centroid's X
        coordinate between rectangle's "left" and "right" coordinates
    :attr __p_determine_height2value_factor_t1__: used while searching for
        column of bar values (the scale) to calculate factor used to convert
        bar's height to real bar's value. This is used to ignore text regions
        with centroids lying too far (along Y axis) from leftmost chart's bar
        "bottom" coordinate
    :attr __p_get_argument_domain_t1__: maximal distance (against Y coordinate)
        between bar's "bottom" and text region candidate specifying description
        of arguments domain
    :attr __p_get_argument_domain_t2__: argument description text region
        maximal allowed centrality factor (0 - ideally central, 0.5 - ideally
        not central)
    :attr __p_get_value_domain_t1__: same as previous option, but used while
        seraching for value domain description text
    :attr __p_get_title_t1__: maximal Y distance between text regions composing
        the title of bar chart"""
    __p_extract_vertical_bars_t1__ = 45
    __p_determine_height2value_factor_t1__ = 10
    __p_get_argument_domain_t1__ = 30
    __p_get_argument_domain_t2__ = 0.3
    __p_get_value_domain_t1__ = 0.4
    __p_get_title_t1__ = 15
    
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

    def __extract_vertical_bars(self, text_used):
        """Extract, create and return list of :class:`VerticalBar` instances
        representing vertical bars of simple bar chart."""
        bars = []
        t1 = self.config(
            'extract_vertical_bars_t1',
            self.__class__.__p_extract_vertical_bars_t1__).asint()
        # Sort rectangles by decreasing coordinate of rectanle bottom
        rect_by_bounds_sorted = sorted(
            self.rect_by_bounds.iterkeys(), key=lambda x: -x[3])
        # Iterate via rectangle bounds starting from lying bottom-most
        for k in rect_by_bounds_sorted:
            # Search for label candidates for current rectangle. Label
            # candidates are text regions whth horizontal centers lying just
            # below the rectangle (but not too far)
            label_candidates = filter(
                lambda x: x[0]>k[0] and x[0]<k[2] and x[1]>k[3] and x[1]-k[3]<=t1,
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
            # Notify that text region is in use
            text_used.add(self.text_by_barycenter[label])
        return bars

    def __determine_height2value_factor(self, bars, text_used):
        """Determine factor used to calculate bar value by multiplying
        resulting factor by bar height. If factor is undeterminable this
        function returns 1 (bar height in pixels is numerically equal to real
        bar value)."""
        t1 = self.config(
            'determine_height2value_factor_t1',
            self.__class__.__p_determine_height2value_factor_t1__).asint()
        # Leave only that text areas that are on the left side of leftmost bar
        leftmost_bar = min(bars, key=lambda x: x.left)
        left = leftmost_bar.left
        bottom = leftmost_bar.bottom
        leftmost_text = filter(lambda x: x[0]<left and x[1]<bottom+t1, self.text_barycenters)
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
                # Notify that text region is in use
                text_used.add(r)
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
    
    def __get_argument_domain(self, bars, text_remaining, text_used):
        """Search for textual description of arguments (bar names)."""
        # Load thresholds from config or class attributes
        t1 = self.config(
            'get_argument_domain_t1',
            self.__class__.__p_get_argument_domain_t1__).asint()
        t2 = self.config(
            'get_argument_domain_t2',
            self.__class__.__p_get_argument_domain_t2__).asfloat()
        # Find maximal bottom coordinate of all bars (this, however, should be
        # rather similar for all bars)
        bottom = max(bars, key=lambda x: x.bottom).bottom
        # Calculate central point
        center = sum([b.barycenter[0] for b in bars]) / len(bars)
        # Get list of text candidates for being a argument domain description
        candidates = filter(lambda x: x.top-bottom<=t1 and x.top-bottom>0, text_remaining)
        if not candidates:
            return
        # Calculate X spread of candidate text areas
        left = min(candidates, key=lambda x: x.left).left
        right = max(candidates, key=lambda x: x.right).right
        # Proceed if bars central X point lies between previously calculated
        # left and right
        if left < center and right > center:
            # Calculate centrality factor of text areas
            f = (center - left) / float(right - left)
            # Check the factor against configurable threshold
            if abs(0.5 - f) < t2:
                domain = []
                # Collect text data
                for c in sorted(candidates, key=lambda x: x.left):
                    domain.append(c.genre.text)
                    text_used.add(c)
                return ' '.join(domain)
    
    def __get_value_domain(self, bars, text_remaining, text_used):
        """Search for textual description of bar values."""
        t1 = self.config(
            'get_value_domain_t1',
            self.__class__.__p_get_value_domain_t1__).asfloat()
        # Use `text_used` because some text area needed here had already been
        # processed in previous steps
        left = min(text_used, key=lambda x: x.left).left
        # Get Y barycenter of highest bar
        center = max(bars, key=lambda x: x.bar.height).barycenter[1]
        # Get vertical text areas lying on the left of leftmost text area used
        candidates = filter(
            lambda x: x.left<left and not x.genre.horizontal,
            text_remaining)
        if not candidates:
            return
        # Further processing is the same as in :meth:`__get_argument_domain`,
        # except the fact that here Y coordinate is used in calculations
        # instead of X
        top = min(candidates, key=lambda x: x.top).top
        bottom = max(candidates, key=lambda x: x.bottom).bottom
        if top < center and bottom > center:
            f = (center - top) / float(bottom - top)
            if abs(0.5 - f) < t1:
                domain = []
                for c in sorted(candidates, key=lambda x: -x.bottom):
                    domain.append(c.genre.text)
                    text_used.add(c)
                return ' '.join(domain)
    
    def __get_title(self, bars, text_remaining, text_used):
        """Search for chart title."""
        t1 = self.config('get_title_t1', self.__class__.__p_get_title_t1__).asint()
        center = self.image.width / 2
        candidates = sorted(
            filter(lambda x: x.left < center and x.right > center, text_remaining),
            key=lambda x: x.top)
        if len(candidates) == 1:
            return candidates[0].genre.text
        else:
            title = [candidates[0].genre.text]
            for i in xrange(len(candidates)-1):
                if candidates[i+1].top - candidates[i].bottom < t1:
                    title.append(candidates[i+1].genre.text)
            return ' '.join(title)

    def parse(self):
        text_used = set()
        # Extract all vertical bars
        bars = self.__extract_vertical_bars(text_used)
        if not bars:
            return
        # Assign values to bars (if not yet assigned)
        if filter(lambda x: x.value is None, bars):
            factor = self.__determine_height2value_factor(bars, text_used)
            if factor:
                for b in bars:
                    if b.value is None:
                        b.value = b.bar.height * factor
        # Search for chart title
        title = self.__get_title(
            bars, self.text.difference(text_used), text_used)
        # Search for argument domain descriptor
        argument_domain = self.__get_argument_domain(
            bars, self.text.difference(text_used), text_used)
        # Search for value domain descriptor
        value_domain = self.__get_value_domain(
            bars, self.text.difference(text_used), text_used)
        # Return results
        return SimpleBarChartResult(bars,
            argument_domain=argument_domain,
            value_domain=value_domain,
            title=title)
