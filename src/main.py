import argparse
import bottle
import config
import logging
import os
import sys
import pymysql
pymysql.install_as_MySQLdb() # Hax for python2 compatibility.
import bottle_mysql


global conf


class unsafe(object):
    func = None

    def __init__(self, fallback=None):
        self.fallback = fallback

    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        try:
            return self.func(*args, **kwargs)
        except:
            return self.fallback


@bottle.get('/hello')
def hello(db):
    db.execute("SELECT 'Hello world!' AS 'result';")
    return db.fetchone()


@bottle.get('/users/:device_id')
def users_all(device_id, db):
    pass


@bottle.get('/users/:device_id/stats')
def users_stats_all(device_id, db):
    ranks = []
    for stat_id, stat in conf.stats.items():
        if stat_id != 'default':
            rank = stat_rank(db=db, stat=stat, device_id=device_id)
            if rank is not None:
                ranks.append({
                    'id': stat_id,
                    'rank': rank
                })
    return {'stats': ranks}


@bottle.get('/users/:device_id/stats/:stat_id')
def users_stat_by_id(device_id, stat_id, db):
    stat = conf.stats.get(stat_id, None)
    if stat is None:
        return not_found("stat '{}' not found.".format(stat_id))
    else:
        rank = stat_rank(db=db, stat=stat, device_id=device_id)
        return {'id': stat_id, 'rank': rank}


@bottle.get('/users/:device_id/achievements')
def users_achievements_all(device_id, db):
    pass


@bottle.get('/users/:device_id/achievements/:achievement_id')
def users_achievement_by_id(device_id, achievement_id, db):
    pass


@bottle.error(404)
def status404(_):
    bottle.response.content_type = 'application/json'
    return '{"error": "not found"}'


@unsafe()
def stat_rank(db, stat, device_id):
    rank = None
    template = "(SELECT count(*) FROM {table} WHERE device_id=%(device_id)s)"
    sub_queries = [template.format(table=table) for table in stat.tables]
    query = "SELECT " + " + ".join(sub_queries) + " AS 'result';"

    db.execute(query, {'device_id': device_id})

    count = db.fetchone()['result']
    thresholds = stat.thresholds
    levels = stat.levels

    if count > 0:
        prev_threshold = 0
        for (idx, threshold) in enumerate(thresholds):
            if prev_threshold < count <= threshold:
                rank = levels[idx]
                break
        if count >= thresholds[-1]:
            rank = levels[-1]
    return rank


def not_found(msg):
    bottle.response.status = 404
    return {'error': msg}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="location of additional configuration file")
    parser.add_argument("-d", "--debug", help="run application in debug mode", action="store_true")

    args = parser.parse_args()

    conf = config.load(path=args.config,
                       fallback_path=os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "../config.json"))

    # DB setup:
    app = bottle.default_app()
    app.catchall = True
    plugin = bottle_mysql.Plugin(dbhost=conf.get('db.host', "localhost"),
                                 dbport=conf.get('db.port', 3306),
                                 dbname=conf.get('db.name', "aware"),
                                 dbuser=conf.get('db.user', "achievement"),
                                 dbpass=conf.get('db.pass'))
    app.install(plugin)

    host = conf.get('app.host', "0.0.0.0")
    port = conf.get('app.port', 8080)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        bottle.run(host=host, port=port, reloader=True)
    else:
        logging.basicConfig(level=logging.INFO)
        bottle.run(host=host, port=port, server="eventlet")  # reload doesn't work with eventlet server
