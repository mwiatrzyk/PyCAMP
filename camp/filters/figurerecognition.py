import os
import logging
import camp.exc as exc

from camp.filters import BaseFilter
from camp.core.colorspace import Convert
from camp.plugins.recognitors import RecognitorPluginBase, ComplexRecognitorPluginBase

log = logging.getLogger(__name__)


class FigureRecognitor(BaseFilter):
    
    def process(self, image, storage=None):
        log.info('running figure recognition process')
        try:
            graphical = storage['TextRecognitor']['graphical']
        except KeyError, e:
            raise exc.CampFilterError("missing in 'storage': %s" % e)

        # Search for complex graphical figures using recognition plugins
        log.debug('searching for complex geometrical figures')
        complex_figures = set()
        plugins = ComplexRecognitorPluginBase.load_all()
        if plugins:
            pass  # TODO

        # Recognize simple graphical figures using recognition plugins
        simple_figures = set()
        plugins = RecognitorPluginBase.load_all()
        if not plugins:
            raise exc.CampError('no geometrical figures recognition plugins found')
        log.debug(
            'performing geometric figure recognition process using '
            'total number of %d recognitors', len(plugins))
        for g in graphical:
            result = []
            for Genre, Recognitor in plugins:
                value = Recognitor().test(g)
                if value:
                    result.append((value, Genre))
            if not result:
                continue
            winner = max(result, key=lambda x: x[0])
            g.genre = winner[1]()
            simple_figures.add(g)
        log.debug('done. Found %d matching simple figures', len(simple_figures))
        
        # Save results for next filter
        storage[self.__class__.__name__] = {
            'simple_figures': simple_figures,
            'complex_figures': complex_figures}
        return image
