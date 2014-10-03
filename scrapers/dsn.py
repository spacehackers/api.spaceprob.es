from __future__ import print_function
import os
import sys
import requests
import redis
import urllib2
from datetime import datetime
from time import sleep, mktime
from json import loads, dumps
from xml.dom.minidom import parse
import xmltodict

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

# fetches our json translation mirror of the dsn/eyes feed
url = 'http://murmuring-anchorage-8062.herokuapp.com/dsn/mirror.json'

def get_dsn_raw():
    """ gets dsn xml feed, converts to json, saves json to redis, returns json """

    # pass the url a param 'r' = timestamp to avoid hitting their cloudfront cache
    timestamp = str(int(mktime(datetime.now().timetuple())))
    response = urllib2.urlopen('http://eyes.nasa.gov/dsn/data/dsn.xml?r=' + timestamp)
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
    dsn_raw = loads(r_server.get('dsn_raw'))

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

    print("updated: " + ", ".join(sorted(list(set(msg)))))

# this is more like a util for the console
def get_current_probes():
    """ list of the current probe names and its length """
    url = 'http://murmuring-anchorage-8062.herokuapp.com/dsn/probes.json'
    for p,v in loads(requests.get(url).text).items():
        return sorted([n for n in v]), len(v)



if __name__ == '__main__':
    get_dsn_raw()  # update the json mirror
    dsn_convert()  # update our 'by spacecraft' schema

