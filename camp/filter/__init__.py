import os
import zlib
import cPickle
import logging

log = logging.getLogger(__name__)


class BaseFilter(object):
    """Base class for filter classes.
    
    :attr __f_enable_caching__: set to ``True`` if caching is enabled for this
        filter class or to ``False`` if caching is disabled for this filter"""
    __f_enable_caching__ = True

    def __init__(self, next_filter=None):
        self.next_filter = next_filter

    def __load_from_cache(self, data, storage=None, key=None):
        filepath = os.path.join('data', 'cache', self.__class__.__name__, key)
        if not os.path.isfile(filepath):
            return
        data = cPickle.loads(zlib.decompress(open(filepath).read()))
        if storage is not None and data.get('storage'):
            storage.update(data['storage'])
        log.info("%s: found cached data for key=%s", self.__class__.__name__, key)
        return data['result']

    def __write_to_cache(self, data, result, storage=None, key=None):
        filepath = os.path.join('data', 'cache', self.__class__.__name__, key)
        dirpath = os.path.dirname(filepath)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        to_be_pickled = {'result': result, 'storage': storage}
        with open(filepath, 'w') as fd:
            fd.write(zlib.compress(cPickle.dumps(to_be_pickled)))

    def __call__(self, data, storage=None, key=None, renew_cache=False):
        if storage and not isinstance(storage, dict):
            raise TypeError("storage: expecting dict or None, found %s (%s)" % (type(storage), storage))
        # Proxy for `process` method: loads from cache or writes data to cache
        # (if caching is enabled)
        def process_proxy(data, storage=None):
            if key and self.__class__.__f_enable_caching__ and not renew_cache:
                if not isinstance(key, basestring):
                    raise TypeError("key: expecting basestring, found %s (%s)" % (type(key), key))
                result = self.__load_from_cache(data, storage=storage, key=key)
                if result:
                    return True, result
            result = self.process(data, storage=storage)
            if key and self.__class__.__f_enable_caching__:
                self.__write_to_cache(data, result, storage=storage, key=key)
            return False, result
        # If results of this filter does not come from cache, cache of further
        # filters must be renewed
        from_cache, result = process_proxy(data, storage=storage)
        if result is None:
            return
        if self.next_filter:
            return self.next_filter(
                result, storage=storage, key=key, renew_cache=not from_cache)
        else:
            return result

    def process(self, data, storage=None):
        raise NotImplementedError()
