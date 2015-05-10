import argparse
import bottle
import config
import errors
import handlers
import logging
import os
import sys
import pymysql
pymysql.install_as_MySQLdb() # Hax for python2 compatibility.
import bottle_mysql

global conf


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
    def regular_achievements():
        achievements = []
        for achievement_id, achievement in conf.achievements.regular.items():
            if achievement_id != 'default':
                badge = handlers.regular_badge_for(db=db, achievement=achievement, device_id=device_id)
                if badge is not None:
                    achievements.append({
                        'id': achievement_id,
                        'badge': badge
                    })
        return achievements

    achievements_handler = {
        'regular': regular_achievements
    }
    filter_by = bottle.request.query.filter
    if not filter_by:
        achievements = {k: v() for k, v in achievements_handler.items()}
    elif filter_by in achievements_handler:
        achievements = {filter_by: achievements_handler[filter_by]()}
    else:
        return errors.error(errors.UnknownAchievementFilter(filter_by))
    return {'achievements': achievements}


@bottle.get('/users/:device_id/achievements/:achievement_id')
def user_achievement_by_id(device_id, achievement_id, db):
    achievement = conf.achievements.regular.get(achievement_id, None)
    if achievement is None:
        return errors.error(errors.UnknownAchievementId(achievement_id))
    else:
        badge = handlers.regular_badge_for(db=db, achievement=achievement, device_id=device_id)
        return {'id': achievement_id, 'badge': badge}


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
