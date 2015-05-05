import json
import jsoncomment
import os
import sys


class Config:
    def __init_config(self, path):
        with open(path) as f:
            for k, v in jsoncomment.JsonComment(json).loads(f.read()).items():
                self.config[k] = v

    def __init__(self, path):
        self.config = {}
        fallback_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "../config.json")
        self.__init_config(fallback_path)
        if path is not None:
            self.__init_config(path)

    def get(self, path, default=None):
        config = self.config
        value = default
        keys = path.split('.')
        for key in keys[:-1]:
            value = config.get(key, None)
            if value is None or not isinstance(config, dict):
                return default
            else:
                config = value
        return config.get(keys[-1], default)


def load(path):
    return Config(path)
