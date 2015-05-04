from bottle import get, run
import argparse


@get('/index')
def index():
    return "Hello world!"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="run application in debug mode", action="store_true")
    parser.add_argument("-p", "--port", help="webserver port to bind", type=int, default=8080)
    parser.add_argument("-ho", "--host", help="webserver host to bind", default="0.0.0.0")

    args = parser.parse_args()

    if args.debug:
        run(host=args.host, port=args.port, reloader=True)
    else:
        run(host=args.host, port=args.port, server="eventlet")  # reload doesn't work with eventlet server
