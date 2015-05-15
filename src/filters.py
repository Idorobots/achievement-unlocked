import errors
from config import Config

filters = {
    "all": lambda c: True,
    "count": lambda c: "count" in c
}


# Utils:
def filter(f, config):
    try:
        fun = filters[f or "all"]
        return Config({a: c for a, c in config.items() if fun(c)})
    except KeyError:
        raise errors.UnknownAchievementFilter(f)
