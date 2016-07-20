from django.conf import settings


class DotDict(dict):
    def __getattr__(self, attr):
        val = self.get(attr)
        if isinstance(val, dict):
            return DotDict(val)
        return val
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


config = DotDict(settings.VERBA_CONFIG)
