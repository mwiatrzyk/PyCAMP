import os
import logging
import ConfigParser

log = logging.getLogger(__name__)


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

    def asstring(self):
        """Return :param:`value` after conversion to string."""
        return str(self)

    def __str__(self):
        """Convert enpacked value to string."""
        return str(self._value)

    def __repr__(self):
        """Get text representation of this object."""
        return "%s(type=%s, value=%s)" %\
            (self.__class__.__name__, type(self.value), str(self))


class Config(object):
    """Application's global configuration placeholder.
    
    :attr ROOT_DIR: specify relative or absolute path to project's root
        directory (the directory of run.py file)
    :attr __cfg_default_config_file__: path to default configuration file. This
        file will be used if no other configuration file path was given"""

    # Constant attributes (shouldn't be changed in subclass)
    ROOT_DIR = '.'

    # Changeable attributes (can be changed in subclass)
    __cfg_default_config_file__ = os.path.join('doc', 'config_default.ini')

    # Private attributes
    __instance = None
    
    def __init__(self, config=None, argv=None):
        """Create new instance of Config class.
        
        :param config: path to configuration file. If not specified, default
            one will be used
        :param argv: dictionary with command line parameters"""
        super(Config, self).__init__()
        config_files = [self.__class__.__cfg_default_config_file__]
        if config:
            config_files.append(config)
        # Create config parser
        cfg = {}
        vars_ = {'rootdir': self.__class__.ROOT_DIR}
        parser = ConfigParser.ConfigParser()
        parser.read(config_files)
        # Read entire config into dictionary
        for s in parser.sections():
            if s == 'argv':
                raise ValueError("'argv' is restricted and cannot be used "
                    "as section name")
            cfg[s] = {}
            for o in parser.options(s):
                cfg[s][o] = parser.get(s, o, vars=vars_)
        # Add command line args to config file
        if argv:
            if not isinstance(argv, dict):
                raise TypeError("argv: expecting dictionary")
            cfg['argv'] = argv
        self._config = cfg
        self._parser = parser

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

    def save(self, path):
        """Write config to given config file."""
        fd = open(path, 'wb')
        try:
            self._parser.write(fd)
        finally:
            fd.close()

    def __call__(self, path, default=None):
        """Allows to access config variables by calling Config instance like a
        function. Returns ``default`` if path is invalid."""
        return self.config(path, default=default, strict=False)

    def __getitem__(self, path):
        """Allows to access config variables in dictionary way. Raises
        ``KeyError`` for invalid paths."""
        return self.config(path, strict=True)
    
    @classmethod
    def instance(cls, config=None, argv=None):
        """Get or create an instance of this class.
        
        :param config: optional path to config file"""
        if not cls.__instance:
            cls.__instance = Config(config=config, argv=argv)
        return cls.__instance
