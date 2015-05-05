import argparse
import bottle
import config
import pymysql
pymysql.install_as_MySQLdb() # Hax for python2 compatibility.
import bottle_mysql


@bottle.get('/hello')
def hello(db):
    db.execute("SELECT 'Hello world!' AS 'result';")
    return db.fetchone()


@bottle.get('/users/:device_id')
def users_all(device_id, db):
    pass


@bottle.get('/users/:device_id/stats')
def users_stats_all(device_id, db):
    pass


@bottle.get('/users/:device_id/stats/:stat_id')
def users_stat_by_id(device_id, stat_id, db):
    pass


@bottle.get('/users/:device_id/achievements')
def users_achievements_all(device_id, db):
    pass


@bottle.get('/users/:device_id/achievements/:achievement_id')
def users_achievement_by_id(device_id, achievement_id, db):
    pass


@bottle.error(404)
def status404(_):
    bottle.response.content_type = 'application/json'
    return '{"result": "Not found!"}'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="location of additional configuration file")
    parser.add_argument("-d", "--debug", help="run application in debug mode", action="store_true")

    args = parser.parse_args()

    config = config.load(args.config)

    # DB setup:
    app = bottle.default_app()
    plugin = bottle_mysql.Plugin(dbhost=config.get('db.host', "localhost"),
                                 dbport=config.get('db.port', 3306),
                                 dbname=config.get('db.name', "aware"),
                                 dbuser=config.get('db.user', "achievement"),
                                 dbpass=config.get('db.pass'))
    app.install(plugin)

    host = config.get('app.host', "0.0.0.0")
    port = config.get('app.port', 8080)
    if args.debug:
        bottle.run(host=host, port=port, reloader=True)
    else:
        bottle.run(host=host, port=port, server="eventlet")  # reload doesn't work with eventlet server
