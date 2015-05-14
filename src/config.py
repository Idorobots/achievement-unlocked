import json
import jsoncomment
import logging


class Config(object):
    def __init_config_from_file(self, path):
        def add_dict(config, d):
            for k, v in d.items():
                kv = config.get(k, None)
                if isinstance(kv, dict) and isinstance(v, dict):
                    add_dict(config=kv, d=v)
                else:
                    config[k] = v
        with open(path) as f:
            add_dict(config=self.__config, d=jsoncomment.JsonComment(json).loads(f.read()))

    def add_defaults(self):
        def add_defaults(subconfig, default):
            for dk, dv in default.items():
                v = subconfig.get(dk, None)
                if v is None:
                    subconfig[dk] = dv
                elif isinstance(dv, dict) and isinstance(v, dict):
                    add_defaults(subconfig=v, default=dv)

        achievements = self.__config['achievements']
        default = achievements.pop('default')
        for a in achievements.values():
            tables = {'tables':  a.pop('tables')}
            if 'no_defaults' not in a or not a['no_defaults']:
                add_defaults(subconfig=a, default=default)
            if 'count' in a:
                add_defaults(subconfig=a['count'], default=tables)

    def transform_achievements(self):
        achievements = self.__config['achievements']
        self.__config['achievements'] = {}
        for a, c in achievements.items():
            for name, handler in c['handlers'].items():
                conf = c.copy()
                del conf['handlers']
                conf['handler'] = handler
                self.__config['achievements'][a + "_" + name] = conf

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

    def __contains__(self, key):
        return key in self.__config.keys()

    def items(self):
        return [(k, Config.sub_config(v)) for k, v in self.__config.items()]

    def keys(self):
        return self.__config.keys()

    def values(self):
        return [Config.sub_config(v) for v in self.__config.values()]

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
    logging.debug("Loading config file: {}".format(path))
    config = Config.from_file(path, fallback_path)
    config.add_defaults()
    config.transform_achievements()
    logging.debug("Config: {}".format(config))
    return config
