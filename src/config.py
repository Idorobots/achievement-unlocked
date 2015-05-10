import json
import jsoncomment
import logging


class ValidationError(Exception):
    def __init__(self, errors):
        errs = []
        for kp, v in errors.items():
            for ks, msgs in v.items():
                k = kp + '.' + ks
                errs += ["{} for '{}'".format(m, k) for m in msgs]

        message = "Validation failed:\n\t{}".format("\n\t".join(errs))
        super(ValidationError, self).__init__(message)


class Config(object):
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

        add_defaults(subconfig=self.__config['achievements'],
                     optional=['thresholds', 'badges', 'handlers'])
        # Remove the default key.
        del self.__config['achievements']['default']

    def validate(self):
        def validate(subconfig, validators):
            errors = {}
            for k in subconfig.keys():
                c = subconfig[k]
                msgs = [m for v, m in validators if not v(k, c)]
                if msgs:
                    errors[k] = msgs
            return errors
        errors = {
            'achievements': validate(
                subconfig = self.__config['achievements'],
                validators=[
                    (
                        lambda k, c: k == 'default' or ('tables' in c and c['tables']),
                        "At least one table should be defined"
                    ),
                    (
                        lambda k, c: len(c['badges']) == len(c['thresholds']) + 1,
                        "Wrong quantity of thresholds defined for specified badges"
                    ),
                    (
                        lambda k, c: 'handlers' in c and c['handlers'],
                        "At least one handler should be defined"
                    )
                ]
            )
        }
        errors = {k: v for k, v in errors.items() if v}
        if errors:
            raise ValidationError(errors)

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
    config.validate()
    config.transform_achievements()
    logging.debug("Config: {}".format(config))
    return config
