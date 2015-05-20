import argparse
import bottle
import config
import db
import errors
import filters
import handlers
import json
import logging
import middleware
import os
import sys


global conf


# App status
@bottle.get('/status')
def status(db):
    db.execute("SELECT 'running' AS 'status';")
    return db.fetchone()


# Ranking
@bottle.get('/ranking', apply=[middleware.intercept])
def ranking_all(db):
    f = filters.filter(bottle.request.query.filter)
    return {a: handlers.dispatch(handlers=handlers.handlers.ranking,
                                 config=f(c),
                                 achievement_id=a,
                                 db=db,
                                 params={'from': bottle.request.query.get("from"),
                                         'to': bottle.request.query.to})
            for a, c in conf.achievements.items()}


@bottle.get('/ranking/:achievement_id', apply=[middleware.intercept])
def ranking_by_id(achievement_id, db):
    f = filters.filter(bottle.request.query.filter)
    c = conf.achievements.get_or_raise(key=achievement_id,
                                       error=errors.UnknownAchievementId(achievement_id))
    return handlers.dispatch(handlers=handlers.handlers.ranking,
                             config=f(c),
                             achievement_id=achievement_id,
                             db=db,
                             params={'from': bottle.request.query.get("from"),
                                     'to': bottle.request.query.to})


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
    f = filters.filter(bottle.request.query.filter)
    return {a: handlers.dispatch(handlers=handlers.handlers.user.ranking,
                                 config=f(c),
                                 achievement_id=a,
                                 db=db,
                                 params={'device_id': device_id,
                                         'from': bottle.request.query.get("from"),
                                         'to': bottle.request.query.to})
            for a, c in conf.achievements.items()}


@bottle.get('/users/:device_id/ranking/:achievement_id', apply=[middleware.intercept])
def user_ranking_by_id(device_id, achievement_id, db):
    f = filters.filter(bottle.request.query.filter)
    c = conf.achievements.get_or_raise(key=achievement_id,
                                       error=errors.UnknownAchievementId(achievement_id))
    return handlers.dispatch(handlers=handlers.handlers.user.ranking,
                             config=f(c),
                             achievement_id=achievement_id,
                             db=db,
                             params={'device_id': device_id,
                                     'from': bottle.request.query.get("from"),
                                     'to': bottle.request.query.to})


@bottle.get('/users/:device_id/achievements', apply=[middleware.intercept])
def user_achievements(device_id, db):
    f = filters.filter(bottle.request.query.filter)
    return {a: handlers.dispatch(handlers=handlers.handlers.user.achievements,
                                 config=f(c),
                                 achievement_id=a,
                                 db=db,
                                 params={'device_id': device_id})
            for a, c in conf.achievements.items()}


@bottle.get('/users/:device_id/achievements/:achievement_id', apply=[middleware.intercept])
def user_achievement_by_id(device_id, achievement_id, db):
    f = filters.filter(bottle.request.query.filter)
    c = conf.achievements.get_or_raise(key=achievement_id,
                                       error=errors.UnknownAchievementId(achievement_id))
    return handlers.dispatch(handlers=handlers.handlers.user.achievements,
                             config=f(c),
                             achievement_id=achievement_id,
                             db=db,
                             params={'device_id': device_id})


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
    plugin = db.Plugin(dbhost=conf.get('db.host', "localhost"),
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
