import os
import logging

from lxml import etree

from camp.util import asfloat, asunicode, dump, BaseDumper
from camp.core import Image
from camp.config import Config
from camp.core.containers import SegmentGroup
from camp.plugins.parsers import ParserPluginBase, ParsingResultBase
from camp.plugins.recognitors.rectangle import RectangleGenre

log = logging.getLogger(__name__)


def _dump_vertical_bars(result, args=None, kwargs=None, dump_dir=None):
    cbounds = Config.instance().config('argv:cbounds', (0, 0, 255)).value
    image = args[0].image.copy()
    for b in result:
        b.display_bounds(image, color=cbounds)
    image.save(os.path.join(dump_dir, 'bars-with-labels.png'))


def _dump_vertical_bars_candidates(result, args=None, kwargs=None, dump_dir=None):
    cbounds = Config.instance().config('argv:cbounds', (0, 0, 255)).value
    image = args[0].copy()
    for b in result:
        b.bar.display_bounds(image, color=cbounds)
        b.label.display_bounds(image, color=cbounds)
    image.save(os.path.join(dump_dir, 'bars-candidates.png'))


class _TextUsedDumper(BaseDumper):
    
    def __precall__(self, args=None, kwargs=None):
        self.text_used = set(args[-1])

    def __postcall__(self, result, args=None, kwargs=None):
        self.text_used = args[-1].difference(self.text_used)


class _DumpYAxisLables(_TextUsedDumper):

    def __call__(self, result, args=None, kwargs=None, dump_dir=None):
        cbounds = Config.instance().config('argv:cbounds', (0, 0, 255)).value
        image = args[0].image.copy()
        labels = SegmentGroup(None)
        labels.segments.update(self.text_used)
        labels.display_bounds(image, color=cbounds)
        image.save(os.path.join(dump_dir, 'y-axis-labels.png'))


class _DumpArgumentDomain(_TextUsedDumper):
    
    def __call__(self, result, args=None, kwargs=None, dump_dir=None):
        cbounds = Config.instance().config('argv:cbounds', (0, 0, 255)).value
        image = args[0].image.copy()
        domain = SegmentGroup(None)
        domain.segments.update(self.text_used)
        if domain.segments:
            domain.display_bounds(image, color=cbounds)
            image.save(os.path.join(dump_dir, 'argument-domain.png'))


class _DumpValueDomain(_TextUsedDumper):
    
    def __call__(self, result, args=None, kwargs=None, dump_dir=None):
        cbounds = Config.instance().config('argv:cbounds', (0, 0, 255)).value
        image = args[0].image.copy()
        domain = SegmentGroup(None)
        domain.segments.update(self.text_used)
        if domain.segments:
            domain.display_bounds(image, color=cbounds)
            image.save(os.path.join(dump_dir, 'value-domain.png'))


class _DumpTitle(_TextUsedDumper):
    
    def __call__(self, result, args=None, kwargs=None, dump_dir=None):
        cbounds = Config.instance().config('argv:cbounds', (0, 0, 255)).value
        image = args[0].image.copy()
        domain = SegmentGroup(None)
        domain.segments.update(self.text_used)
        if domain.segments:
            domain.display_bounds(image, color=cbounds)
            image.save(os.path.join(dump_dir, 'title.png'))


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
        self.argument_domain = asunicode(argument_domain or '')
        self.value_domain = asunicode(value_domain or '')
        self.title = asunicode(title or '')

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
    :attr __p_extract_vertical_bars_t2__: allowed difference measured in pixels
        between "bottom" of two neighboring bars
    :attr __p_extract_vertical_bars_t3__: allowed difference (in pixels)
        between "width" of two neighboring bars
    :attr __p_extract_vertical_bars_t4__: allowed difference (in pixels)
        between two bar distances
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
    __p_extract_vertical_bars_t2__ = 2
    __p_extract_vertical_bars_t3__ = 2
    __p_extract_vertical_bars_t4__ = 2
    __p_determine_height2value_factor_t1__ = 10
    __p_get_argument_domain_t1__ = 30
    __p_get_argument_domain_t2__ = 0.3
    __p_get_value_domain_t1__ = 0.4
    __p_get_title_t1__ = 15
    
    def __init__(self, *args, **kwargs):
        super(SimpleBarChartParser, self).__init__(*args, **kwargs)
        # Map of text.barycenter -> text
        self.text_by_barycenter = dict([((t.barycenter, t.top), t) for t in self.text])
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
    
    @dump(_dump_vertical_bars)
    def __extract_vertical_bars(self, text_used):
        """Extract, create and return list of :class:`VerticalBar` instances
        representing vertical bars of simple bar chart."""
        bars = []
        t1 = self.config('extract_vertical_bars_t1').asint()
        t2 = self.config('extract_vertical_bars_t2').asint()
        t3 = self.config('extract_vertical_bars_t3').asint()
        t4 = self.config('extract_vertical_bars_t4').asint()
        # Check if there are any rectangles in the image
        if not self.rectangles:
            log.debug('no rectangles found')
            return []
        # Sort rectangles by decreasing coordinate of rectanle bottom
        rect_by_bounds_sorted = sorted(
            self.rect_by_bounds.iterkeys(), key=lambda x: -x[3])
        # Iterate via rectangle bounds starting from lying bottom-most
        for k in rect_by_bounds_sorted:
            # Search for label candidates for current rectangle. Label
            # candidates are text regions whth horizontal centers lying just
            # below the rectangle (but not too far)
            label_candidates = filter(
                lambda x: x[0][0]>k[0] and x[0][0]<k[2] and x[1]>k[3] and x[1]-k[3]<=t1,
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
        # Dump candidates
        dump(_dump_vertical_bars_candidates)(lambda x: bars)(self.image)
        # Sort bars by left property (ascending)
        log.debug('number of bar candidates: %d', len(bars))
        bars_sorted = sorted(bars, key=lambda x: x.bar.left)
        # Keeps distances between bars (all values should be the same)
        distances = []
        # Validate bars
        for i in xrange(len(bars_sorted)-1):
            # Compare bottoms of two neighboring bars
            if abs(bars_sorted[i].bar.bottom - bars_sorted[i+1].bar.bottom) > t2:
                log.debug('failed on checking bar bottoms with t2=%s', t2)
                return []
            # Compare widths of two neighboring bars
            if abs(bars_sorted[i].bar.width - bars_sorted[i+1].bar.width) > t3:
                log.debug('failed on checking bar widths with t3=%s', t3)
                return []
            # Calculate distance between neighboring bars to be checked later
            distances.append(bars_sorted[i+1].bar.left - bars_sorted[i].bar.right)
        # Validate distances between neighboring bars
        for i in xrange(len(distances)-1):
            if abs(distances[i] - distances[i+1]) > t4:
                log.debug('failed on checking bar distances with t4=%s', t4)
                return []
        return bars
    
    @dump(_DumpYAxisLables)
    def __determine_height2value_factor(self, bars, text_used):
        """Determine factor used to calculate bar value by multiplying
        resulting factor by bar height. If factor is undeterminable this
        function returns 1 (bar height in pixels is numerically equal to real
        bar value)."""
        t1 = self.config('determine_height2value_factor_t1').asint()
        # Leave only that text areas that are on the left side of leftmost bar
        leftmost_bar = min(bars, key=lambda x: x.left)
        left = leftmost_bar.left
        bottom = leftmost_bar.bottom
        leftmost_text = filter(lambda x: x[0][0]<left and x[0][1]<bottom+t1, self.text_barycenters)
        # If text area could not be found, return neutral factor (1)
        if not leftmost_text:
            return 1.0
        scale = []
        # Calculate average Y position where all bars starts
        startpoint = int(sum([b.bar.bottom for b in bars]) / float(len(bars)))
        # Find in previously created `leftmost_text` sequence the region that
        # is closest to leftmost bar
        t = max(leftmost_text, key=lambda x: x[0][0]+x[0][1])
        # Find all text areas lying in vertical column formed by `t`. Sort it
        # in decreasing order of `bottom` position as well
        remaining = sorted(
            filter(lambda x: t[0][0]>x.left and t[0][0]<x.right and x.top<t[0][1], self.text),
            key=lambda x: -x.bottom)
        # Try to convert text to float
        for r in remaining:
            try:
                # Try to convert text to float number
                tmp = asfloat(r.genre.text)
                # If there is `0` in the Y axis values use its barycenter as
                # startpoint for more accurate results
                if tmp == 0.0:
                    text_used.add(r)
                    startpoint = r.barycenter[1]
                if not tmp:
                    continue
                # Add parsed value and its pixel height to list of results
                scale.append((tmp, abs(r.barycenter[1]-startpoint)))
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
    
    @dump(_DumpArgumentDomain)
    def __get_argument_domain(self, bars, text_remaining, text_used):
        """Search for textual description of arguments (bar names)."""
        # Load thresholds from config or class attributes
        t1 = self.config('get_argument_domain_t1').asint()
        t2 = self.config('get_argument_domain_t2').asfloat()
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
    
    @dump(_DumpValueDomain)
    def __get_value_domain(self, bars, text_remaining, text_used):
        """Search for textual description of bar values."""
        t1 = self.config('get_value_domain_t1').asfloat()
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
    
    @dump(_DumpTitle)
    def __get_title(self, bars, text_remaining, text_used):
        """Search for chart title."""
        t1 = self.config('get_title_t1').asint()
        center = self.image.width / 2
        candidates = sorted(
            filter(lambda x: x.left < center and x.right > center, text_remaining),
            key=lambda x: x.top)
        if not candidates:
            return
        if len(candidates) == 1:
            text_used.add(candidates[0])
            return candidates[0].genre.text
        else:
            title = [candidates[0].genre.text]
            text_used.add(candidates[0])
            for i in xrange(len(candidates)-1):
                if candidates[i+1].top - candidates[i].bottom < t1:
                    title.append(candidates[i+1].genre.text)
                    text_used.add(candidates[i+1])
            return ' '.join(title)

    def parse(self):
        log.info('assuming that input image is simple bar chart image')
        text_used = set()
        # Extract all vertical bars
        log.debug('searching for chart bars')
        bars = self.__extract_vertical_bars(text_used)
        if len(bars) < 2:
            log.info('no bars found: image is not a simple bar chart image')
            return
        log.debug('done. Found total number of %d bars', len(bars))
        # Assign values to bars (if not yet assigned)
        if filter(lambda x: x.value is None, bars):
            log.debug('determining conversion factor for bars: pixel height *'
                ' factor -> real value')
            factor = self.__determine_height2value_factor(bars, text_used)
            log.debug('done. Calculated factor: %1.3f', factor)
            if factor:
                for b in bars:
                    if b.value is None:
                        b.value = b.bar.height * factor
        # Search for chart title
        log.debug('searching for bar title text')
        title = self.__get_title(
            bars, self.text.difference(text_used), text_used)
        log.debug('search results: %s', title)
        # Search for argument domain descriptor
        log.debug('searching for argument (bar name) domain description')
        argument_domain = self.__get_argument_domain(
            bars, self.text.difference(text_used), text_used)
        log.debug('search results: %s', argument_domain)
        # Search for value domain descriptor
        log.debug('searching for value (bar height) domain descriptor')
        value_domain = self.__get_value_domain(
            bars, self.text.difference(text_used), text_used)
        log.debug('search results: %s', value_domain)
        # Return results
        return SimpleBarChartResult(bars,
            argument_domain=argument_domain,
            value_domain=value_domain,
            title=title)
