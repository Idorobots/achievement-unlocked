import logging

class unsafe(object):
    func = None

    def __init__(self, fallback=None):
        self.fallback = fallback

    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        try:
            return self.func(*args, **kwargs)
        except Exception as e:
            logging.error("Caught an exception: {}".format(e))
            return self.fallback
