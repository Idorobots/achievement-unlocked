import logging

# DB utils
def execute(db, query, *args, **kwargs):
    logging.debug("Executing SQL query: '{}', {}, {}".format(query, args, kwargs))
    return db.execute(query, *args, **kwargs)
