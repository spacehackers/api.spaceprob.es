import os
import redis
from flask import Flask
from util import json, jsonp
from json import loads

app = Flask(__name__)

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

@app.route('/<probe>')
@jsonp
@json
def detail(probe):
    """ returns list of data we have for this probe """

    # todo: lookup data in redis
    try:
        data = loads(r_server.get(probe))
    except:  # type error?
        return {'Error': 'spacecraft not found'}, 404

    return data, 200


@app.route('/')
@jsonp
@json
def index():
    """ returns list of all space probes in db """

    # todo: get list of space probles from redis
    probe_names = r_server.keys()

    # include link into api in response
    spaceprobes = {'spaceprobes': [p for p in probe_names]}

    return spaceprobes, 200


if __name__ == '__main__':
    app.debug = True
    app.run()