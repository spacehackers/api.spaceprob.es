from __future__ import print_function
import os
import redis
import ephem
import requests
from flask import Flask, render_template, redirect, jsonify
from json import loads, dumps
from util import json, jsonp, support_jsonp
from scrapers.dsn import get_dsn_raw

app = Flask(__name__)
REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

@app.route('/')
def hello():
    return redirect("/dsn/probes.json", code=302)

@app.route('/dsn/mirror.json')
@json
def dsn_mirror():
    """ a json view of the dsn xml feed """
    dsn = loads(r_server.get('dsn_raw'))
    return {'dsn': dsn }, 200

@app.route('/dsn/probes.json')
@support_jsonp
def dsn_by_probe():
    """ dsn data by probe """
    dsn_by_probe = loads(r_server.get('dsn_by_probe'))
    return jsonify({'dsn_by_probe': dsn_by_probe})

# for feeding the spaceprobes website
@app.route('/distances.json')
@support_jsonp
def all_probe_distances():
    # first get list of all probes from the webiste
    url = 'http://probes.natronics.org/probes.json'
    url = 'http://0.0.0.0:4000/probes.json'
    all_probes_website = loads(requests.get(url).text)

    # get probes according to DSN
    dsn = loads(r_server.get('dsn_by_probe'))

    # see what's missing
    distances = {}
    for probe in all_probes_website:  # loop thru all probes that appear on website
        dsn_name = probe['dsn_name']
        slug = probe['slug']

        if dsn_name and dsn_name in dsn:
            distances[slug] = dsn[dsn_name]['uplegRange']

        elif 'distance' in probe and probe['distance']:
            # this probe's distance is hard coded at website, add that
            distances[slug] = probe['distance']

        elif 'orbit_planet' in probe and probe['orbit_planet']:
            # this probes distance is same as a planet, so use pyephem

            # find distance to planet
            if probe['orbit_planet'] == 'Venus':
                m = ephem.Venus()
            if probe['orbit_planet'] == 'Mars':
                m = ephem.Mars()

            if m:
                m.compute()
                earth_distance = m.earth_distance * 149597871  # convert from AU to kilometers
                distances[slug] = earth_distance


    return jsonify({'spaceprobe_distances': distances})


@app.route('/planets.json')
@support_jsonp
def planet_distances():
    """ dsn data by probe """
    meters_per_au = 149597870700

    planet_ephem = [ephem.Mercury(), ephem.Venus(), ephem.Mars(), ephem.Saturn(), ephem.Jupiter(), ephem.Uranus(), ephem.Neptune(), ephem.Pluto()]
    planets = {}
    for p in planet_ephem:
        p.compute()
        planets[p.name] = p.earth_distance *  meters_per_au / 10000  # km

    return jsonify({'distance_from_earth_km': planets})


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
@support_jsonp
@json
def detail(probe):
    """ returns list of data we have for this probe from wolfram alpha
        url = /<probe_name>
        ie
        </Cassini>
    """
    return get_detail(probe), 200


@app.route('/probes/<probe>/<field>/')
@support_jsonp
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
@support_jsonp
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
