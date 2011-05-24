import os

from subprocess import Popen, PIPE
from camp.config import Config


class OCRPluginBase(object):
    """Base class for external OCR plugins.
    
    :attr __ocr_command__: command used to execute external OCR tool. Can have
        ``%(foo)s`` like substitutions
    :attr __ocr_priority__: priority of this OCR plugin. Lower values means
        higher priorities. This attribute is used to sort plugin classes to use
        it in desired order
    :attr __ocr_enabled__: setting to ``True`` will enable this OCR plugin,
        setting to ``False`` will disable it"""
    __ocr_command__ = None
    __ocr_priority__ = 0
    __ocr_enabled__ = True

    def __init__(self, working_dir):
        """Create new instance of OCR recognitor.
        
        :param working_dir: specifies working directory"""
        super(OCRPluginBase, self).__init__()
        self.working_dir = working_dir
        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir)
    
    def execute(self, **params):
        """Execute external OCR application by executing
        :attr:`__ocr_command__` command. Optional parameters are used to
        replace ``%(foo)s``-like template variables in provided command.
        Returns ``True`` if execution succeeds or ``False`` otherwise.
        
        :rtype: bool"""
        cmd = self.__class__.__ocr_command__
        p = Popen(
            cmd % params if params else cmd,
            shell=True, bufsize=1024,
            stdout=PIPE, stderr=PIPE, close_fds=True)
        if p.wait() != 0:
            return False
        return True

    def create_infile(self, segment, angle=None):
        """Creates input file for external OCR tool. Return value will be used
        as :param:`infile` parameter of :meth:`get_result`.
        
        :param segment: a segment to be recognized
        :param angle: specifies rotation angle. Usefull when vertical text
            segments need to be recognized as well"""
        raise NotImplementedError()

    def get_result(self, segment, infile):
        """Execute :attr:`__ocr_command__` command in subprocess and await for
        it to finish. Return value will be used as return value of
        :meth:`perform` and as argument of :meth:`recognized`.
        
        :param segment: a segment to be recognized
        :param infile: input file. This is result of :meth:`create_infile`"""
        raise NotImplementedError()
    
    def recognized(self, result):
        """Used to check if result produced by external OCR tool is correct (is
        a meaningful text, not a mess).
        
        :param result: return value of :meth:`get_result`"""
        raise NotImplementedError()

    def perform(self, segment, angles=None):
        """Begin text recognition process on given segment taken from image.
        
        :param angles: sequence of rotation angles. If given, recognition
            process is repeated up to ``len(angles)`` times and the segment is
            rotated by the current angle before recognition process starts.
            Loop is terminated once text is recognized or once there are no
            more angles to use."""
        for a in (angles or [None]):
            infile = self.create_infile(segment, angle=a)
            result = self.get_result(segment, infile)
            if self.recognized(result):
                return result

    def config(self, key, default=None):
        """Get value of configuration parameter named ``key``. If ``default``
        evaluates to ``False``, class attribute with prefix ``__ocr_`` and
        postfix ``__`` is used (if exists)."""
        key_ = "plugins:ocr:%s:%s" % (self.__class__.__name__, key)
        return Config.instance().config(
            key_, default or getattr(self.__class__, "__ocr_%s__" % key, None))

    @classmethod
    def load_all(cls):
        """Load all available and enabled OCR plugin classes and return it as
        list sorted by plugin priority."""
        config = Config.instance()
        result = []
        for entry in os.listdir(os.path.join(*tuple(__name__.split('.')))):
            if entry.startswith('_'):
                continue
            if not entry.endswith('.py'):
                continue
            class_name = ''.join([n.title() for n in entry[:-3].split('_')])
            config_prefix = "plugins:ocr:%s" % class_name
            module = __import__(
                "%s.%s" % (__name__, entry[:-3]), fromlist=[class_name])
            class_ = getattr(module, class_name)
            if config("%s:enabled" % config_prefix, class_.__ocr_enabled__).asbool():
                result.append((class_, config_prefix))
        result = sorted(
            result,
            key=lambda x: config("%s:priority" % x[1], x[0].__ocr_priority__).asint())
        return [r[0] for r in result]
