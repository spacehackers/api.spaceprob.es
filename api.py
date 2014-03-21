import os
import redis
from flask import Flask
from util import json, jsonp
from json import loads

app = Flask(__name__)

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r = redis.StrictRedis.from_url(REDIS_URL)

@app.route('/<probe>')
@jsonp
@json
def detail(probe):
    """ returns list of data we have for this probe """

    # todo: lookup data in redis
    """
    try:
        data = loads(r.get(probe))
    except TypeError:  # typeerror?
        pass
        # todo: return 404 nicely here
    """

    # fake data!
    data = {'Probe name': probe,
            'Launch Date': 'Thu Mar 20 17:16:17 PDT 2014',
            'distance_from_earth': 20000,
            'last downlink station': 'Goldstone',
            'last downlink time': 'Thu Mar 20 17:16:17 PDT 2014',
            'Mission Phase':'cruise',
            'orbit_no':6,
            'orbit_body':'Saturn'
            }

    return data, 200


@app.route('/')
@jsonp
@json
def list():
    """ returns list of all space probes in db """

    # todo: get list of space probles from redis
    probe_names = ['Cassini', 'Voyager 1', 'Voyager 2','MRO']

    # include link into api in response
    spaceprobes = {'spaceprobes': [p.replace(" ", "-") for p in probe_names]}

    return spaceprobes, 200


if __name__ == '__main__':
    app.debug = True
    app.run()