from __future__ import print_function
import os
import sys
import requests
import redis
import urllib2
from time import sleep
from json import loads, dumps
from xml.dom.minidom import parse
import xmltodict


REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

# fetches from our mirror of the dsn/eyes feed
url = 'http://murmuring-anchorage-8062.herokuapp.com/dsn/mirror.json'

def get_dsn_raw():
    """ a json view of the dsn xml feed """

    response = urllib2.urlopen('http://eyes.nasa.gov/dsn/data/dsn.xml')
    dom=parse(response)

    dsn_data = {}
    for node in dom.childNodes[0].childNodes:

        if not  hasattr(node, 'tagName'):  # useless nodes
            continue

        # dsn feed is strange: dishes should appear inside station nodes but don't
        # so converting entire xml doc to dict loses the station/probe relation
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

    r_server.set('dsn_raw', dumps(dsn_data))

    return dsn_data


def dsn_convert():
    """ read our json mirror of dsn raw feed and remix+save
        into our 'by probe' schema """

    # fetch+ooad dsn from our json mirror
    try:
        print("trying %s" % url)
        req = requests.get(url)
    except requests.exceptions.RequestException as e:    # This is the correct syntax
        print(e)
        sys.exit(1)

    if req.status_code == requests.codes.ok:
        try:
            dsn_raw = loads(req.text)['dsn']
        except ValueError:
            print("could not load dsn data from %s" % url)
            sys.exit(1)
    else:
        print("status code not ok")
        print(str(req.status_code))

    dsn_by_probe = loads(r_server.get('dsn_by_probe'))

    msg = []
    for station in dsn_raw:
        for dish_attr in dsn_raw[station]:

            timeUTC, timeZoneOffset = (dsn_raw[station]['timeUTC'], dsn_raw[station]['timeZoneOffset'])
            dish_list = dsn_raw[station]['dishes']

            for dish in dish_list:

                dish_name, downSignal, upSignal, target = (dish['@name'], dish['downSignal'], dish['upSignal'], dish['target'])
                last_contact, updated = (dish['@created'], dish['@updated'])

                # if only a single downSignal it is a dict, if multiples it is a list, make them all lists:
                if type(downSignal).__name__ == 'dict':
                    downSignal = [downSignal]
                if type(upSignal).__name__ == 'dict':
                    upSignal = [upSignal]
                if type(target).__name__ == 'dict':
                    target = [target]

                for d in target:  # sometimes it talks to > 1 target at a time

                    probe = d['@name']

                    dsn_by_probe.setdefault(probe, {})

                    probe_data = {k[1:]:v for k,v in d.items()}  # just removing the @ signs here

                    dsn_by_probe[probe]['downlegRange'] = d['@downlegRange']
                    dsn_by_probe[probe]['uplegRange'] = d['@uplegRange']
                    dsn_by_probe[probe]['rtlt'] = d['@rtlt']
                    dsn_by_probe[probe]['last_conact'] = last_contact
                    dsn_by_probe[probe]['last_dish'] = dish_name
                    dsn_by_probe[probe]['updated'] = updated

                r_server.set('dsn_by_probe', dumps(dsn_by_probe))

                msg.append(probe)

    print("updated: " + ", ".join(list(set(msg))))

if __name__ == '__main__':
    get_dsn_raw()  # update the json mirror
    dsn_convert()  # update our 'by spacecraft' schema

