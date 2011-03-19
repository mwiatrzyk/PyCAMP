
class BaseFilter(object):
    """Base class for filter classes."""

    def __init__(self, next_filter=None):
        self.next_filter = next_filter

    def __call__(self, data):
        result = self.process(data)
        if result is None:
            return
        if self.next_filter:
            return self.next_filter(result)
        else:
            return result

    def process(self, data):
        raise NotImplementedError()
