import os
import redis
from flask import Flask, render_template
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
    except TypeError:  # type error?
        return {'Error': 'spacecraft not found'}, 404  # this doesn't work i dunno


@app.route('/api/guide/')
def guide():
    """ html api guide data viewer thingy
        at </api/guide/>
    """
    probe_details = {}
    for probe in r_server.keys():
        probe_details[probe] = get_detail(probe)
    kwargs = {'probe_details':probe_details}
    return render_template('guide.html', **kwargs)


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
