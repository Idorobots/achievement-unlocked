import argparse
import bottle
import config
import errors
import filters
import handlers
import json
import logging
import middleware
import os
import sys
import pymysql
pymysql.install_as_MySQLdb() # Hax for python2 compatibility.
import bottle_mysql

global conf


# App status
@bottle.get('/status')
def status(db):
    db.execute("SELECT 'running' AS 'status';")
    return db.fetchone()


# Ranking
@bottle.get('/ranking', apply=[middleware.intercept])
def ranking_all(db):
    config = filters.filter(bottle.request.query.filter, conf.achievements)
    return {a: handlers.dispatch_ranking(None, a, c, db) for a, c in config.items()} # FIXME Get rid of the None


@bottle.get('/ranking/:achievement_id', apply=[middleware.intercept])
def ranking_by_id(achievement_id, db):
    config = conf.achievements.get(achievement_id)
    if config is None:
        raise errors.UnknownAchievementId(achievement_id)
    # NOTE Can't return arrays to Bottle :(
    bottle.response.content_type = "application/json"
    return json.dumps(handlers.dispatch_ranking(None, achievement_id, config, db)) # FIXME Get rid of the None


# Achievements
@bottle.get('/achievements', apply=[middleware.intercept])
def achievements_all(db):
    pass


@bottle.get('/achievements/:achievement_id', apply=[middleware.intercept])
def achievements_by_id(achievement_id, db):
    pass


# Users
@bottle.get('/users/:device_id', apply=[middleware.intercept])
def user_all(device_id, db):
    ranking = user_ranking(device_id, db)
    achievements = user_achievements(device_id, db)
    return {"ranking": ranking,
            "achievements": achievements}


@bottle.get('/users/:device_id/ranking', apply=[middleware.intercept])
def user_ranking(device_id, db):
    config = filters.filter(bottle.request.query.filter, conf.achievements)
    return {a: handlers.dispatch_user_ranking(device_id, a, c, db) for a, c in config.items()}


@bottle.get('/users/:device_id/ranking/:achievement_id', apply=[middleware.intercept])
def user_ranking_by_id(device_id, achievement_id, db):
    config = conf.achievements.get(achievement_id)
    if config is None:
        raise errors.UnknownAchievementId(achievement_id)
    return handlers.dispatch_user_ranking(device_id, achievement_id, config, db)


@bottle.get('/users/:device_id/achievements', apply=[middleware.intercept])
def user_achievements(device_id, db):
    filter_by = bottle.request.query.filter
    config = filters.filter(filter_by, conf.achievements)
    if config is None:
        raise errors.UnknownAchievementFilter(filter_by)
    return {
        a: handlers.dispatch_achievement(device_id, a, c, db) for a, c in config.items()
    }


@bottle.get('/users/:device_id/achievements/:achievement_id', apply=[middleware.intercept])
def user_achievement_by_id(device_id, achievement_id, db):
    config = conf.achievements.get(achievement_id)
    if config is None:
        raise errors.UnknownAchievementId(achievement_id)
    return handlers.dispatch_achievement(device_id, achievement_id, config, db)


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

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

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
        bottle.run(host=host, port=port, reloader=True)
    else:
        bottle.run(host=host, port=port, server="eventlet")  # reload doesn't work with eventlet server
