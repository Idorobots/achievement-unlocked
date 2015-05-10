import argparse
import bottle
import config
import errors
import filters
import handlers
import logging
import os
import sys
import pymysql
pymysql.install_as_MySQLdb() # Hax for python2 compatibility.
import bottle_mysql

global conf

# App status
@bottle.get('/status')
def hello(db):
    db.execute("SELECT 'running' AS 'status';")
    return db.fetchone()


# Ranking
@bottle.get('/ranking')
def ranking_all(db):
    pass


@bottle.get('/ranking/:achievement_id')
def raknig_by_id(achievement_id, db):
    pass


# Users
@bottle.get('/users/:device_id')
def user_all(device_id, db):
    pass


@bottle.get('/users/:device_id/ranking')
def user_ranking(device_id, db):
    try:
        config = filters.filter(bottle.request.query.filter, conf.achievements)
        return {a: handlers.dispatch_ranking(device_id, a, c, db) for a, c in config.items()}
    except errors.AppError as e:
        return e.to_dict()


@bottle.get('/users/:device_id/ranking/:achievement_id')
def user_ranking_by_id(device_id, stat_id, db):
    try:
        config = conf.achievements.get(achievement_id, None)
        return handlers.dispatch_ranking(device_id, achievement_id, config, db)

    except errors.AppError as e:
        return e.to_dict()


@bottle.get('/users/:device_id/achievements')
def user_achievements(device_id, db):
    try:
        config = filters.filter(bottle.request.query.filter, conf.achievements)
        return {a: handlers.dispatch_achievement(device_id, a, c, db) for a, c in config.items()}
    except errors.AppError as e:
        return e.to_dict()


@bottle.get('/users/:device_id/achievements/:achievement_id')
def user_achievement_by_id(device_id, achievement_id, db):
    try:
        config = conf.achievements.get(achievement_id, None)
        return handlers.dispatch_achievement(device_id, achievement_id, config, db)

    except errors.AppError as e:
        return e.to_dict()


# Misc
@bottle.error(404)
def status404(_):
    bottle.response.content_type = 'application/json'
    return '{"error": "not found"}'


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
