import errors


filters = {
    "all": lambda c: True,
    "count": lambda c: "count" in c,
    "procent": lambda c: "procent" in c,
    "time": lambda c: "time" in c,
    "funny": lambda c: "funny" in c
}


# Utils:
def filter(f):
    try:
        fun = filters[f or "all"]
        return lambda config: {k: (h, config[k]) for k, h in config['handlers'].items() if fun(k)}
    except KeyError:
        raise errors.UnknownAchievementFilter(f)
