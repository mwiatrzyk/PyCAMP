import logging
import camp.exc as exc

from camp.core import Image
from camp.util import asfloat
from camp.filter import BaseFilter
from camp.core.containers import SegmentGroup, BaseGenre
from camp.plugins.recognitors.rectangle import RectangleGenre
from camp.plugins.parsers import ParserPluginBase, ParsingResultBase

log = logging.getLogger(__name__)


class Parser(BaseFilter):
    """Filter that performs parsing of input image trying several parsers from
    :module:`camp.plugins.parsers`."""
    
    def process(self, image, storage=None):
        log.info('performing parsing step')

        prev_results = storage.get('ObjectRecognitor')
        if not prev_results:
            raise exc.CampFilterError(
                "ObjectRecognitor filter must be called first")

        text = prev_results.get('text')
        simple_figures = prev_results.get('simple_figures')
        complex_figures = prev_results.get('complex_figures')
        
        for Parser in ParserPluginBase.load_all():
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
