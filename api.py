from __future__ import print_function
import os
import redis
from flask import Flask, render_template, redirect
from json import loads, dumps
from util import json, jsonp
from scrapers.dsn import get_dsn_raw

app = Flask(__name__)
REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

@app.route('/')
def hello():
    return redirect("/dsn/probes.json", code=302)

@app.route('/dsn/mirror.json')
@jsonp
@json
def dsn_mirror():
    """ a json view of the dsn xml feed """
    dsn = loads(r_server.get('dsn_raw'))
    return {'dsn': dsn }, 200

@app.route('/dsn/probes.json')
# @jsonp
@json
def dsn_by_probe():
    """ a json view of the dsn xml feed """
    dsn_by_probe = loads(r_server.get('dsn_by_probe'))
    return {'dsn_by_probe': dsn_by_probe}, 200


# the rest of this is like wolfram alpha data or something..

def get_detail(probe):
    """ returns list of data we have for this probe
        url = /<probe_name>
    """
    try:
        wolframalpha = loads(r_server.get('wolframalpha'))
        detail = wolframalpha[probe]
        return detail
    except TypeError:  # type error?
        return {'Error': 'spacecraft not found'}, 404  # this doesn't work i dunno


@app.route('/probes/guide/')
def guide():
    """ html api guide data viewer thingy
        at </probes/guide/>
    """
    try:
        wolframalpha = loads(r_server.get('wolframalpha'))
        kwargs = {'probe_details':wolframalpha}
        return render_template('guide.html', **kwargs)
    except:
        return redirect("dsn/probes.json", code=302)

@app.route('/probes/<probe>/')
@jsonp
@json
def detail(probe):
    """ returns list of data we have for this probe from wolfram alpha
        url = /<probe_name>
        ie
        </Cassini>
    """
    return get_detail(probe), 200


@app.route('/probes/<probe>/<field>/')
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


@app.route('/probes/')
@jsonp
@json
def index():
    """ returns list of all space probes in db
        url = /
    """
    probe_names = [k for k in loads(r_server.get('wolframalpha'))]
    return {'spaceprobes': [p for p in probe_names]}, 200



if __name__ == '__main__':
    app.debug = True
    app.run()
