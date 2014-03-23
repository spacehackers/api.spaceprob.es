import os
import redis
from flask import Flask
from util import json, jsonp
from json import loads

app = Flask(__name__)
REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

def get_detail(probe):
    """ returns list of data we have for this probe
        url = /<probe_name>
    """
    try:
        detail = loads(r_server.get(probe))
        return detail
    except:  # type error?
        return {'Error': 'spacecraft not found'}, 404

@app.route('/<probe>/')
@jsonp
@json
def detail(probe):
    """ returns list of data we have for this probe
        url = /<probe_name>
        ie
        </Cassini>
    """
    return get_detail(probe), 200

@app.route('/<probe>/<field>/')
@jsonp
@json
def single_field(probe, field):
    """ returns data for single field
        url = /<probe_name>/<field>
        ie
        </Cassini/mass>
    """
    field_value = get_detail(probe)
    return {field: field_value[field]}, 200

@app.route('/')
@jsonp
@json
def index():
    """ returns list of all space probes in db
        url = /
    """
    probe_names = r_server.keys()
    return {'spaceprobes': [p for p in probe_names]}, 200


if __name__ == '__main__':
    app.debug = True
    app.run()
