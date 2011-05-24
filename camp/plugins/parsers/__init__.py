import os
import logging

from lxml import etree
from camp.config import Config

log = logging.getLogger(__name__)


class ParsingResultBase(object):
    """Class representing parsing results of input data.
    
    :attr __pr_input_type__: description of input data type recognized"""
    __pr_input_type__ = u'UNKNOWN'
    
    def __init__(self):
        """Create new instance of ParsingResultBase class."""
        super(ParsingResultBase, self).__init__()
        self._exml = self.__create_result_xml()
    
    def __create_result_xml(self):
        """Create skeleton of resulting XML document."""
        root = etree.Element('Result')
        root.attrib.update({
            'Type': self.__class__.__pr_input_type__,
            'Version': '1.0'})
        head = etree.SubElement(root, 'Header')
        body = etree.SubElement(root, 'Content')
        return root
    
    @property
    def root(self):
        """Root node of result XML."""
        return self._exml

    @property
    def header(self):
        """Header node of result XML."""
        return self.root.xpath('/Result/Header')[0]

    @property
    def content(self):
        """Content node of result XML."""
        return self.root.xpath('/Result/Content')[0]
    
    @property
    def type_(self):
        """Shortcut for class' type described in :attr:`__pr_input_type__`."""
        return self.__class__.__pr_input_type__

    def tostring(self):
        """Convert parsing result in XML format to string."""
        return etree.tostring(self._exml, pretty_print=True)

    def save(self, path):
        """Save parsing results given by :meth:`tostring` in file.
        
        :param path: path to result file"""
        log.info('writing output file: %s', path)
        fd = open(path, 'w')
        try:
            fd.write(self.tostring().encode('utf-8'))
        finally:
            fd.close()


class ParserPluginBase(object):
    """Base class for plugins performing parsing of input data after the input
    had been preprocessed.
    
    :attr __p_enabled__: enable or disable plugin
    :attr __p_priority__: plugin's priority (the lowest value - the highes
        priority)"""
    __p_enabled__ = True
    __p_priority__ = 0
    
    def __init__(self, image, text, simple_figures, complex_figures):
        """Create new instance of this parser plugin.
        
        :param image: input image, possibly after some sort of processing
        :param text: set of text regions extracted from input image
        :param simple_figures: set of simple figures found in input image
        :param complex_figures: set of complex figures found in input image"""
        super(ParserPluginBase, self).__init__()
        self.image = image
        self.text = text
        self.simple_figures = simple_figures
        self.complex_figures = complex_figures
    
    def parse(self):
        """Override in subclass to provide parsing algorithm. This method must
        return instance of :class:`ParsingResultBase` class if parser was able
        to parse input image. Any other return value signalizes the need to
        proceed to next parser."""
        raise NotImplementedError()
    
    def config(self, key, default=None):
        """Get value of configuration parameter named ``key``. If ``default``
        evaluates to ``False``, class attribute with prefix ``__p_`` and
        postfix ``__`` is used (if exists)."""
        key_ = "plugins:parsers:%s:%s" % (self.__class__.__name__, key)
        return Config.instance().config(
            key_, default or getattr(self.__class__, "__p_%s__" % key, None))

    @classmethod
    def load_all(cls):
        """Load all available parsing plugins and return as list of
        :class:`ParserPluginBase` subclasses. List is sorted by plugin
        priority. Disabled plugins won't be present in the list."""
        config = Config.instance()
        result = []
        for entry in os.listdir(os.path.join(*tuple(__name__.split('.')))):
            if entry.startswith('_'):
                continue
            if not entry.endswith('.py'):
                continue
            class_name = "%sParser" % ''.join([n.title() for n in entry[:-3].split('_')])
            config_prefix = "plugins:parsers:%s" % class_name
            module = __import__(
                "%s.%s" % (__name__, entry[:-3]), fromlist=[class_name])
            class_ = getattr(module, class_name)
            if config("%s:enabled" % config_prefix, class_.__p_enabled__).asbool():
                result.append((class_, config_prefix))
        result = sorted(
            result,
            key=lambda x: config("%s:priority" % x[1], x[0].__p_priority__).asint())
        return [r[0] for r in result]
