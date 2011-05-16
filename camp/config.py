import os
import ConfigParser


class ScalarProxy(object):
    
    def __init__(self, value):
        self._value = value
    
    @property
    def value(self):
        return self._value

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return "%s(type=%s, value=%s)" %\
            (self.__class__.__name__, type(self.value), str(self))


class Config(object):
    """Application's configuration placeholder."""
    __instance = None
    
    def __init__(self, config=None):
        """Create new instance of Config class.
        
        :param config: name of config file to be used instead of default one"""
        super(Config, self).__init__()
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
        if isinstance(result, dict):
            return dict(result)
        else:
            return ScalarProxy(result)

    def __call__(self, path, strict=True):
        """Allows to access config variables by calling Config instance like a
        function."""
        return self.config(path, strict=strict)

    def __getitem__(self, path):
        """Allows to access config variables in dictionary way."""
        return self.config(path, strict=True)
    
    @classmethod
    def instance(cls, config=None):
        """Create a singleton instance of Application class.
        
        :param config: optional path to config file"""
        if not cls.__instance:
            cls.__instance = Config(config=config)
        return cls.__instance
