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


@bottle.get('/users/:device_id/ranking')
def user_ranking(device_id, db):
    pass


@bottle.get('/users/:device_id/ranking/:achievement_id')
def user_ranking_by_id(device_id, stat_id, db):
    pass


@bottle.get('/users/:device_id/achievements')
def user_achievements(device_id, db):
    def regular_badges():
        badges = []
        for badge_id, badge_config in conf.badges.regular.items():
            if badge_id != 'default':
                badge = regular_badge_for(db=db, subconfig=badge_config, device_id=device_id)
                if badge is not None:
                    badges.append({
                        'id': badge_id,
                        'badge': badge
                    })
        return badges

    badges_handler = {
        'regular': regular_badges
    }
    filter_by = bottle.request.query.filter
    print('filter ' + filter_by)
    if not filter_by:
        badges = {k: v() for k, v in badges_handler.items()}
    elif filter_by in badges_handler:
        badges = {filter_by: badges_handler[filter_by]()}
    else:
        return error("malformed query param: '{}'".format(filter_by), code=400)
    return {'badges': badges}


@bottle.get('/users/:device_id/achievements/:achievement_id')
def user_achievement_by_id(device_id, achievement_id, db):
    badge_config = conf.badges.regular.get(achievement_id, None)
    if badge_config is None:
        return error("unknown id: '{}'".format(achievement_id), code=404)
    else:
        badge = regular_badge_for(db=db, subconfig=badge_config, device_id=device_id)
        return {'id': achievement_id, 'badge': badge}


@bottle.error(404)
def status404(_):
    bottle.response.content_type = 'application/json'
    return '{"error": "not found"}'


@unsafe()
def regular_badge_for(db, subconfig, device_id):
    badge = None
    template = "(SELECT count(*) FROM {table} WHERE device_id=%(device_id)s)"
    sub_queries = [template.format(table=table) for table in subconfig.tables]
    query = "SELECT " + " + ".join(sub_queries) + " AS 'result';"

    db.execute(query, {'device_id': device_id})

    count = db.fetchone()['result']
    thresholds = subconfig.thresholds
    levels = subconfig.levels

    if count > 0:
        prev_threshold = 0
        for (idx, threshold) in enumerate(thresholds):
            if prev_threshold < count <= threshold:
                badge = levels[idx]
                break
        if count >= thresholds[-1]:
            badge = levels[-1]
    return badge


def error(msg, code):
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
