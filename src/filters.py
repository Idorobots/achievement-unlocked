import middleware


filters = {
    "all": lambda c: True,
    "count": lambda c: "count" in c
}


# Utils:
@middleware.unsafe()
def filter(f, config):
    fun = filters[f or "all"]
    return {a: c for a, c in config.items() if fun(c)}
