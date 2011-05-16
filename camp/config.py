import os
import ConfigParser


class ScalarProxy(object):
    """Wrapper on values read from config files. It contains methods for easily
    conversion to desired types."""
    
    def __init__(self, value):
        """Enpack ``value`` in ScalarProxy class instance.
        
        :param value: object of any type"""
        self._value = value
    
    @property
    def value(self):
        """Enpacked value in original form."""
        return self._value
    
    def asbool(self):
        """Return :param:`value` after conversion to bool."""
        if isinstance(self.value, bool):
            return self.value
        if self.value in ('True', 'true', 'Yes', 'yes', 1):
            return True
        if self.value in ('False', 'false', 'No', 'no', 0):
            return False
        return bool(self.value)

    def asint(self):
        """Return :param:`value` after conversion to int."""
        return int(self.value)

    def asfloat(self):
        """Return :param:`value` after conversion to float."""
        return float(self.value)

    def __str__(self):
        """Convert enpacked value to string."""
        return str(self._value)

    def __repr__(self):
        """Get text representation of this object."""
        return "%s(type=%s, value=%s)" %\
            (self.__class__.__name__, type(self.value), str(self))


class Config(object):
    """Application's global configuration placeholder."""
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
            cfg[s] = {}
            for o in parser.options(s):
                cfg[s][o] = parser.get(s, o)
        self._config = cfg

    def config(self, path, default=None, strict=False):
        """Get value matching ``path`` from loaded config file. Returned value
        can be either entire section or single value depending on ``path``
        argument.
        
        :param path: config entry path, f.e. ``foo:bar:baz``
        :param strict: if True, KeyError is raised if ``path`` does not exist
            in config file"""
        if not self._config:
            return ScalarProxy(default)
        splitted = path.rsplit(':', 1)
        result = self._config.get(path)
        if not result:
            result = self._config.get(splitted[0], {}).get(splitted[1])
            if not result:
                if strict:
                    raise KeyError(path)
                else:
                    return ScalarProxy(default)
        if isinstance(result, dict):
            return dict(result)
        else:
            return ScalarProxy(result)

    def __call__(self, path, default=None):
        """Allows to access config variables by calling Config instance like a
        function. Returns ``default`` if path is invalid."""
        return self.config(path, default=default, strict=False)

    def __getitem__(self, path):
        """Allows to access config variables in dictionary way. Raises
        ``KeyError`` for invalid paths."""
        return self.config(path, strict=True)
    
    @classmethod
    def instance(cls, config=None):
        """Create a singleton instance of Application class.
        
        :param config: optional path to config file"""
        if not cls.__instance:
            cls.__instance = Config(config=config)
        return cls.__instance
