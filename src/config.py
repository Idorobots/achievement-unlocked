import json
import jsoncomment


class Config:
    def __init_config_from_file(self, path):
        def add_dict(config, d):
            for k, v in d.items():
                if k in config and isinstance(config[k], dict) and isinstance(v, dict):
                    add_dict(config=config[k], d=v)
                else:
                    config[k] = v
        with open(path) as f:
            add_dict(config=self.__config,
                     d=jsoncomment.JsonComment(json).loads(f.read()))

    def add_defaults(self):
        def add_defaults(subconfig, optional, default_key='default'):
            default = subconfig[default_key]
            for k, v in subconfig.items():
                if k != default_key:
                    for opt in optional:
                        if opt not in v:
                            v[opt] = default[opt]
        add_defaults(subconfig=self.__config['stats'],
                     optional=['thresholds', 'levels'])

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
            return Config.sub_config(config[keys[-1]])
        except KeyError:
            raise KeyError(path)

    def get(self, path, default=None):
        try:
            return self.__getitem__(path)
        except KeyError:
            return default

    def __getattr__(self, key):
        return Config.sub_config(self.__config[key])

    def __str__(self):
        return self.__config.__str__()

    def __repr__(self):
        return self.__config.__repr__()

    @staticmethod
    def sub_config(value):
        if isinstance(value, dict):
            return Config(value)
        else:
            return value

    @staticmethod
    def from_file(path, fallback_path):
        config = Config({})
        config.__init_config_from_file(fallback_path)
        if path is not None:
            config.__init_config_from_file(path)
        return config


def load(path, fallback_path):
    config = Config.from_file(path, fallback_path)
    config.add_defaults()
    return config
