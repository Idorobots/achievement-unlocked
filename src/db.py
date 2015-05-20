import logging
import functools

# Hax for python3 compatibility.
import pymysql
pymysql.install_as_MySQLdb()
import bottle_mysql


def with_logging(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        logging.debug("Calling {}, {}".format(args, kwargs))
        return f(*args, **kwargs)
    return wrapper

# Hax for logging.
pymysql.cursors.Cursor.execute = with_logging(pymysql.cursors.Cursor.execute)

# Might as well...
Plugin = bottle_mysql.Plugin
