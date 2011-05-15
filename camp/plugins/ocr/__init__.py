import os

from subprocess import Popen, PIPE


class OCRPluginBase(object):
    """Base class for external OCR plugins.
    
    :attr __ocr_command__: command used to execute external OCR tool. Can have
        ``%(foo)s`` like substitutions"""
    __ocr_command__ = None

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

    @classmethod
    def load(cls, name, args=None, kwargs=None):
        """Import plugin of given name, create its instance using provided args
        and kwargs and return it.
        
        :param name: plugin name. If name is invalid, ImportError will be
            raised
        :param args: positional arguments tuple
        :param kwargs: keyword arguments dictionary"""
        clsname = ''.join([n.title() for n in name.split('_')])
        module = __import__("camp.plugins.ocr.%s" % name, fromlist=[clsname])
        return getattr(module, clsname)(*(args or tuple()), **(kwargs or {}))
