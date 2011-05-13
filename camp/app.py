import os
import logging
import ConfigParser

from hashlib import md5
from camp.core import Image
from camp.filter.quantization import Quantizer
from camp.filter.segmentation import Segmentizer
from camp.filter.objrecognize import ObjectRecognitor
from camp.filter.featuredetection import ImageFeatureDetector

log = logging.getLogger(__name__)


class Application(object):
    __instance = None
    
    def __init__(self, config=None):
        """Create new instance of Application class.
        
        :param config: name of config file to be used instead of default one"""
        super(Application, self).__init__()
        config_files = [
            config or 'config.ini',
            os.path.join('doc', 'config_default.ini')]
        self.__load_config(config_files)

    def __load_config(self, configs):
        """Loads entire config file by searching for files listed in
        :param:`configs` and opening the first one that is found.
        
        :param configs: list of config file path names"""
        cfg = {}
        parser = ConfigParser.ConfigParser()
        parser.read(configs)
        for s in parser.sections():
            next_ = cfg
            for k in s.split(':'):
                next_ = next_.setdefault(k, {})
            for o in parser.options(s):
                next_[o] = parser.get(s, o)
        self._config = cfg

    def config(self, path, strict=True):
        """Get value matching ``path`` from loaded config file. Returned value
        can be either entire section or single value depending on ``path``
        argument.
        
        :param path: config entry path, f.e. ``foo:bar:baz``
        :param strict: if True, KeyError is raised if ``path`` does not exist
            in config file"""
        result = self._config
        if not result:
            return {}
        for k in path.split(':'):
            result = result.get(k)
            if not result:
                if strict:
                    raise KeyError(path)
                else:
                    return {}
        return dict(result)

    @classmethod
    def instance(cls, config=None):
        """Create a singleton instance of Application class.
        
        :param config: optional path to config file"""
        if not cls.__instance:
            cls.__instance = Application(config=config)
        return cls.__instance

    def run(self, source, dest, **options):
        """Execute application and return exit code.
        
        :param source: source image file path
        :param dest: destination data file path"""
        # Calculate md5 checksum of a file (used by caching utility)
        key = md5(open(source).read()).hexdigest()

        # Load source image
        source = Image.load(source).convert('RGB')
        
        # Create filter stack
        f = None
        f = ObjectRecognitor(next_filter=f)
        f = Segmentizer(next_filter=f)
        #f = ImageFeatureDetector(next_filter=f)
        f = Quantizer(next_filter=f, config=self.config('filter:Quantizer'))
        
        key=None
        # Execute filter stack
        f(source, storage={}, key=key).save(dest)
