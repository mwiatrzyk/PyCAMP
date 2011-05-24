import logging
import camp.exc as exc

from camp.core import Image
from camp.util import asfloat
from camp.filters import BaseFilter
from camp.core.containers import SegmentGroup, BaseGenre
from camp.plugins.recognitors.rectangle import RectangleGenre
from camp.plugins.parsers import ParserPluginBase, ParsingResultBase

log = logging.getLogger(__name__)


class Parser(BaseFilter):
    """Filter that performs parsing of input image trying several parsers from
    :module:`camp.plugins.parsers`."""
    
    def process(self, image, storage=None):
        log.info('running parsing process')
        try:
            text = storage['TextRecognitor']['text']
            simple_figures = storage['FigureRecognitor']['simple_figures']
            complex_figures = storage['FigureRecognitor']['complex_figures']
        except KeyError, e:
            raise exc.CampFilterError("missing in 'storage': %s" % e)
        
        for Parser in ParserPluginBase.load_all():
            log.debug('executing parser: %s', Parser)
            parser = Parser(image, text, simple_figures, complex_figures)
            try:
                result = parser.parse()
            except Exception:
                log.exception('exception while executing parser %s:', Parser)
                continue
            if not isinstance(result, ParsingResultBase):
                log.warning(
                    'result from parser %s is not instance of '
                    'ParsingResultBase - skipping to another parser', Parser)
                continue
            return result
        else:
            log.warning('no parser could recognize input image')

        return ParsingResultBase()
