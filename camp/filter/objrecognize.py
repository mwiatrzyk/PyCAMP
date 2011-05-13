import os
import math
import logging

import camp.plugins.ocr as ocr_plugins

from subprocess import Popen, PIPE

from camp.filter import BaseFilter
from camp.core import Image
from camp.core.containers import SegmentGroup, Text
from camp.core.colorspace import Convert

log = logging.getLogger(__name__)


def distance(a, b):
    #return math.sqrt((b[0]-a[0])**2 + (b[1]-a[1])**2)
    return abs(b[0]-a[0]) + abs(b[1]-a[1])


def right(a, b):
    dist = b[0] - a[0]
    if dist < 0:
        return 2**32
    return dist + abs(b[1]-a[1])


class ObjectRecognitor(BaseFilter):
    __f_enable_caching__ = False

    def __find_background(self, image, segments):
        """Find and return "background" segments. A segment is said to be
        background if one of its bounds matches corresponding image bound."""
        def is_background(x):
            return\
                x.left == 0 or\
                x.top == 0 or\
                x.right == image.width-1 or\
                x.bottom == image.height-1
        return set(filter(is_background, segments))

    def extract_text(self, image, segments_, ocr='tesseract', max_width=40,
                    max_height=30, letter_delta=6, word_delta=12,
                    min_word_area=20, max_vertical_height=30):
        """Find and return group of segments composing textual information.
        
        :param max_width: maximal width of potential letter
        :param max_height: maximal height of potential letter
        :param letter_delta: maximal distance between two letters
        :param word_delta: maximal distance between two words
        :param min_word_area: minimal area of pixels composing word (used
            to remove minor segments before OCR procedure)
        :param max_vertical_height: maximal height of vertical letters"""

        def box_filter(segments):
            """Removes segments which bounds does not fit in given maximal
            bounds. Used to leave segments that are mostly like to be text
            segments."""
            candidates = set()
            for s in segments:
                if s.width > max_width or s.height > max_height:
                    continue
                candidates.add(s)
            return candidates

        def clear_letters(segments):
            """Removes internal segments from letters like ``P`` or ``B``. This
            is done by removing segments that have none neighbours from outside
            of ``segments`` sequence."""
            candidates = set()
            indices = set([s.index for s in segments])
            for s in segments:
                for n in s.neighbours:
                    if n not in indices:
                        candidates.add(s)
                        break
                else:
                    segments_.remove(s)  # Letter internal segments won't be used
            return candidates
        
        def merge_segments(segments):
            """Group letter candidates into larger connected structures using
            same algorithm as the one used to extract segments from the
            image.""" 
            tmp = set(segments)
            segment_map = dict([(s.index, s) for s in segments])
            indices = set(segment_map.keys())
            groups = []
            while tmp:
                segment = tmp.pop()
                stack = [segment]
                group = SegmentGroup(len(groups))
                group.segments.add(segment)
                while stack:
                    s = stack.pop()
                    for n in s.neighbours:
                        if n in indices:
                            tmp.discard(segment_map[n])
                            indices.remove(n)
                            stack.append(segment_map[n])
                            group.segments.add(segment_map[n])
                groups.append(group)
            return groups
        
        def extract_text_regions(segments):
            """Extracts regions that are supposed to be text regions and
            perform OCR recognition on text region candidates. """
            
            def group(bound_map, delta, horizontal=True):
                Y1 = 1 if horizontal else 0
                Y2 = 3 if horizontal else 2
                X1 = 0 if horizontal else 1
                X2 = 2 if horizontal else 3
                bound_set = set(bound_map.keys())
                groups = set()
                while bound_set:
                    cur = min(bound_set, key=lambda x: x[0]+x[1])
                    hmin, hmax = cur[Y1], cur[Y2]
                    bound_set.remove(cur)
                    group = SegmentGroup(0)
                    group.segments.add(bound_map[cur])
                    while bound_set:
                        #candidates = filter(lambda x: x[0]-cur[2]>=0 and x[0]-cur[2]<=delta, bound_set)
                        candidates = sorted(filter(lambda x: x[X1]>=cur[X1] and x[X1]-cur[X2]<=delta, bound_set), key=lambda x: -x[Y2])
                        for c in candidates:
                            if c[Y1] > hmax or c[Y2] < hmin:
                                continue
                            group.segments.add(bound_map[c])
                            bound_set.remove(c)
                            cur = c
                            break
                        else:
                            break
                    #to_be_added = filter(lambda x: x[0]<=group.right and x[2]>=group.left and x[1]<=group.bottom and x[3]>=group.top, bound_set)
                    #for b in to_be_added:
                    #    group.segments.add(bound_map[b])
                    #    bound_set.remove(b)
                    groups.add(group)
                return groups
            
            horizontal_text = set()
            vertical_text = set()

            # Group letters into words (horizontal)
            words = group(dict([(s.bounds, s) for s in segments]), letter_delta)

            # Group words into sentences (horizontal)
            sentences = group(dict([(w.bounds, w) for w in words if len(w.area) > min_word_area]), word_delta)

            # Split set into horizontal text region candidates and vertical
            # text region candidates
            for s in sentences:
                if s.width <= max_vertical_height:
                    vertical_text.add(s)
                else:
                    horizontal_text.add(s)
            
            # Group letters into words (vertical)
            words = group(dict([(s.bounds, s) for s in vertical_text]), letter_delta, horizontal=False)

            # Group words into sentences (vertical)
            sentences = group(dict([(s.bounds, s) for s in words]), word_delta, horizontal=False)
            
            return horizontal_text.union(sentences)
        
        # Workflow
        candidates = box_filter(segments_)
        candidates = clear_letters(candidates)
        candidates = merge_segments(candidates)
        candidates = extract_text_regions(candidates)
        
        # Perform OCR recognition using external OCR process
        result = set()
        OCR = ocr_plugins.load_plugin(ocr)
        ocr = OCR(os.path.join('data', 'ocr', ocr))
        for c in candidates:
            text = ocr.perform(c, angles=[0, 270])
            if text:
                c.genre = Text(text=text)
                result.add(c)

        return result

    def process(self, image, storage=None):
        segments = storage.get('Segmentizer', {}).get('segments')
        if not segments:
            raise ValueError("no segments found: did you call Segmentizer filter first?")

        # Text recognition process
        log.info('performing text regions search and OCR recognition process')
        text_regions = self.extract_text(
            image, segments,
            ocr='tesseract',
            max_width=40, max_height=30,
            letter_delta=6, word_delta=12, min_word_area=20,
            max_vertical_height=30)
        log.info('found %d text regions', len(text_regions))
        
        # Now split set of segment into two disjoined sets - one containing
        # textual segments, and one containing graphical segments
        log.info('splitting set of segments into textual and graphical segment sets')
        textual = set()
        graphical = set()
        for s in segments:
            if isinstance(s.genre, Text):
                textual.add(s)
            else:
                graphical.add(s)
        
        print len(graphical)

        image = Image.create(image.mode, image.width, image.height)
        for s in text_regions:
            s.display(image)
            s.display_bounds(image)

        return image

        background = self.__find_background(segments)
        img = Image.create(image.mode, image.width, image.height)
        for b in background:
            b.display(img)
        return img
        #maxc = max([c for c in image.colors()], key=lambda x: x[0])
        #max_distance = distance((0, 0), (image.width-1, image.height-1)) #math.sqrt(image.width**2 + image.height**2)
        return image
        '''color = (0, 0, 0)
        tmp = set(segments[color])
        starting = min(tmp, key=lambda x: x.bounds[0]*x.bounds[1])
        tmp.remove(starting)
        i = 0
        while tmp:
            #starting.display(image)
            next_ = min(tmp, key=lambda x: right(starting.barycenter, x.barycenter))
            #print next_.barycenter
            tmp.remove(next_)
            starting = next_
            i += 1
            if i >= 50:
                break
        #starting.display(image)
        #next_.display(image)
        for i, a in enumerate(segments[color]):
            continue
            b = min(segments[color], key=lambda x: distance(x.barycenter, a.barycenter) if x is not a else max_distance)
            if i < 1:
                continue
            a.display(image)
            b.display(image)
            return image'''
        for color in segments:
            print color, Convert.rgb2hsv(color), sum([len(o.area) for o in segments[color]]) / float(image.width*image.height) * 100
        image = Image.create(image.mode, image.width, image.height)
        for o in segments[(94, 94, 94)]: #background:
            o.display(image)
        return image
