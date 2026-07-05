import time
import redis
from flask import Flask

app = Flask(__name__)
cache = redis.Redis(host="redis", port=6379)  # "redis" = the service name


def hit_count():
    retries = 5
    while True:
        try:
            return cache.incr("hits")
        except redis.exceptions.ConnectionError:
            if retries == 0:
                raise
            retries -= 1
            time.sleep(0.5)


@app.route("/")
def index():
    count = hit_count()
    return f"Hello! This page has been viewed {count} time(s).\n"
