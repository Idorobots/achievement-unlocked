import errors
import middleware

filters = {
    "all": lambda x: True
}

# Utils:
@middleware.unsafe()
def filter(f, config):
    fun = filters[f or "all"]
    return {a: c for (a, c) in config.items() if fun(a)}
