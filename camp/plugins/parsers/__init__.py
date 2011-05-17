import os

from camp.config import Config


class ParsingResultBase(object):
    __pr_input_type__ = u'UNKNOWN'
    
    def tostring(self):
        return u"Type of image: %s" % self.__class__.__pr_input_type__.upper()

    def save(self, path):
        fd = open(path, 'w')
        try:
            fd.write(self.tostring().encode('utf-8'))
        finally:
            fd.close()


class ParserPluginBase(object):
    __pp_enabled__ = True
    __pp_priority__ = 0
    
    def __init__(self, text, simple_figures, complex_figures):
        super(ParserPluginBase, self).__init__()
        self.text = text
        self.simple_figures = simple_figures
        self.complex_figures = complex_figures
    
    def parse(self):
        raise NotImplementedError()

    @classmethod
    def load_all(cls):
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
            if config("%s:enabled" % config_prefix, class_.__pp_enabled__).asbool():
                result.append((class_, config_prefix))
        result = sorted(
            result,
            key=lambda x: config("%s:priority" % x[1], x[0].__pp_priority__).asint())
        return [r[0] for r in result]
