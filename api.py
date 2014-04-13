from __future__ import print_function
import os
import urllib2
import redis
import xmltodict
from xml.dom.minidom import parse
from flask import Flask, render_template, redirect
from json import loads
from util import json, jsonp

app = Flask(__name__)
REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)


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
    wolframalpha = loads(r_server.get('wolframalpha'))
    kwargs = {'probe_details':wolframalpha}
    return render_template('guide.html', **kwargs)


@app.route('/probes/<probe>/')
@jsonp
@json
def detail(probe):
    """ returns list of data we have for this probe
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
    probe_names = r_server.keys()
    return {'spaceprobes': [p for p in probe_names]}, 200

@app.route('/')
def hello():
    return redirect("/probes/guide/", code=302)

@app.route('/dsn.json')
@app.route('/dump/dsn.json')  # back compat
@jsonp
@json
def dsn():
    """ a json view of the dsn xml feed """
    response = urllib2.urlopen('http://eyes.nasa.gov/dsn/data/dsn.xml')
    dom=parse(response)

    dsn_data = {}
    for node in dom.childNodes[0].childNodes:

        if not  hasattr(node, 'tagName'):  # useless nodes
            continue

        # dsn feed is strange: dishes should appear inside station nodes but don't
        # so converting entire xml doc to dict loses the station/spacecraft relation
        # so have to parse node by node to grab station THEN convert dish node to dict
        if node.tagName == 'station':
            xmltodict.parse(node.toxml())
            station = node.getAttribute('friendlyName')
            dsn_data.setdefault(station, {})
            dsn_data[station]['friendlyName'] = node.getAttribute('friendlyName')
            dsn_data[station]['timeUTC'] = node.getAttribute('timeUTC')
            dsn_data[station]['timeZoneOffset'] = node.getAttribute('timeZoneOffset')

        if node.tagName == 'dish':
            dsn_data[station].setdefault('dishes', []).append(xmltodict.parse(node.toxml())['dish'])

    return {'dsn': dsn_data}, 200


if __name__ == '__main__':
    app.debug = True
    app.run()
