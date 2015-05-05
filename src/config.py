import json
import jsoncomment


class Config:
    def __init_config_from_file(self, path):
        with open(path) as f:
            for k, v in jsoncomment.JsonComment(json).loads(f.read()).items():
                self.__config[k] = v

    def __init__(self, config):
        self.__config = config

    def __getitem__(self, path):
        config = self.__config
        keys = path.split('.')
        try:
            for key in keys[:-1]:
                value = config[key]
                if isinstance(value, dict):
                    config = value
                else:
                    raise KeyError
            return Config.subConfig(config[keys[-1]])
        except KeyError:
            raise KeyError(path)

    def get(self, path, default=None):
        try:
            return self.__getitem__(path)
        except KeyError:
            return default

    def __getattr__(self, key):
        return Config.subConfig(self.__config[key])

    def __str__(self):
        return self.__config.__str__()

    def __repr__(self):
        return self.__config.__repr__()

    @staticmethod
    def subConfig(value):
        if isinstance(value, dict):
            return Config(value)
        else:
            return value

    @staticmethod
    def fromfile(path, fallback_path):
        config = Config({})
        config.__init_config_from_file(fallback_path)
        if path is not None:
            config.__init_config_from_file(path)
        return config


def load(path, fallback_path):
    assert(fallback_path is not None)
    return Config.fromfile(path, fallback_path)
