import copy
import datetime
import functools
import json
import jsoncomment
import logging
import re


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
                    subconfig[dk] = copy.copy(dv)
                elif isinstance(dv, dict) and isinstance(v, dict):
                    add_defaults(subconfig=v, default=dv)

        def time_threshold(threshold):
            hours_p = re.compile("^(\d+)\s*h\s*$", re.IGNORECASE)
            days_p = re.compile("^(\d+)\s*d\s*$", re.IGNORECASE)
            weaks_p = re.compile("^(\d+)\s*w\s*$", re.IGNORECASE)
            p = hours_p.match(threshold)
            if p:
                return datetime.timedelta(hours=int(p.group(1)))
            p = days_p.match(threshold)
            if p:
                return datetime.timedelta(days=int(p.group(1)))
            p = weaks_p.match(threshold)
            if p:
                return datetime.timedelta(weeks=int(p.group(1)))
            raise Exception("Unknown threshold type in '{}'".format(threshold))
        achievements = self.__config['achievements']
        default = achievements.pop('default')
        for a in achievements.values():
            tables = 'tables' in a and {'tables': a.pop('tables')} or {}
            if 'no_defaults' not in a or not a['no_defaults']:
                add_defaults(subconfig=a, default=default)
            if 'count' in a:
                add_defaults(subconfig=a['count'], default=tables)
            if 'procent' in a:
                add_defaults(subconfig=a['procent'], default=tables)
            if 'time' in a:
                add_defaults(subconfig=a['time'], default=tables)
            a['time']['thresholds'] = [time_threshold(t) for t in a['time']['thresholds']]

    def __init__(self, config):
        self.__config = config

    def __getitem__(self, key):
        try:
            v = functools.reduce(dict.__getitem__, key.split('.'), self.__config)
            return Config.subconfig(v)
        except KeyError:
            raise KeyError(key)

    def get_or_raise(self, key, error):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise error

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getattr__(self, key):
        return Config.subconfig(self.__config[key])

    def __str__(self):
        return self.__config.__str__()

    def __repr__(self):
        return self.__config.__repr__()

    def __contains__(self, key):
        return key in self.__config.keys()

    def items(self):
        return [(k, Config.subconfig(v)) for k, v in self.__config.items()]

    def keys(self):
        return self.__config.keys()

    def values(self):
        return [Config.subconfig(v) for v in self.__config.values()]

    @staticmethod
    def subconfig(value):
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
    logging.debug("Config: {}".format(config))
    return config
