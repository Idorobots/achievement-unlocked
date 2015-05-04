import argparse
import bottle
import pymysql
pymysql.install_as_MySQLdb() # Hax for python2 compatibility.
import bottle_mysql

@bottle.get('/hello')
def hello(db):
    db.execute("SELECT 'Hello world!' AS 'result';")
    return db.fetchone()

@bottle.error(404)
def status404(_):
    bottle.response.content_type = 'application/json'
    return '{"result": "Not found!"}'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="run application in debug mode", action="store_true")
    parser.add_argument("-p", "--port", help="webserver port to bind", type=int, default=8080)
    parser.add_argument("-ho", "--host", help="webserver host to bind", default="0.0.0.0")

    # DB args:
    parser.add_argument("-dh", "--db-host", help="database host", default="localhost")
    parser.add_argument("-du", "--db-user", help="database username", default="achievement")
    parser.add_argument("-dp", "--db-pass", help="database password", default="unlocked")
    parser.add_argument("-db", "--db-name", help="database name", default="achievements")

    args = parser.parse_args()

    # DB setup:
    app = bottle.default_app()
    plugin = bottle_mysql.Plugin(dbhost = args.db_host,
                                 dbuser = args.db_user,
                                 dbpass = args.db_pass,
                                 dbname = args.db_name)
    app.install(plugin)

    if args.debug:
        bottle.run(host=args.host, port=args.port, reloader=True)
    else:
        bottle.run(host=args.host, port=args.port, server="eventlet")  # reload doesn't work with eventlet server
