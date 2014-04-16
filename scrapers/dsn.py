from __future__ import print_function
import os
import sys
import json
import requests
import redis

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

url = 'http://murmuring-anchorage-8062.herokuapp.com/dsn.json'
data = json.loads(requests.get(url).text)['dsn']

# log when we updated the database
this_dsn = data
last_dsn = r_server.get('last_dsn')
if this_dsn == data:
    print('dns feed has not changed')
    sys.exit()  # nothing to do
if this_dsn != data:
    r_server.set('last_dsn', last_dsn)
    print("dsn has changed, database updated")

dsn_data = {}
for station in data:
    for dish_attr in data[station]:
        timeUTC, timeZoneOffset = (data[station]['timeUTC'], data[station]['timeZoneOffset'])
        dish_list = data[station]['dishes']

        for dish in dish_list:
            dish_name, downSignal, upSignal = (dish['@name'], dish['downSignal'], dish['upSignal'])
            last_contact, updated = (dish['@created'], dish['@updated'])

            # if only a single downSignal it is a dict, if multiples it is a list, make them all lists:
            if type(downSignal).__name__ == 'dict':
                downSignal = [downSignal]
            if type(upSignal).__name__ == 'dict':
                upSignal = [upSignal]

            for d in downSignal:
                if not d['@spacecraft'] or not d['@frequency']: continue  # sometimes there is no uplink/downlink

                spacecraft = d['@spacecraft']  # now can build a struct based on spacecraft
                dsn_data.setdefault(spacecraft, {})
                spacecraft_data = {k[1:]:v for k,v in d.items()}  # just removing the @ signs here

                del(spacecraft_data['spacecraft'])  # redundant here

                dsn_data[spacecraft]['last_downSignal'] = spacecraft_data
                dsn_data[spacecraft]['last_downSignal_station'] = station
                dsn_data[spacecraft]['last_downSignal_dish'] = dish_name
                dsn_data[spacecraft]['last_downSignal_date'] = last_contact


            for d in upSignal:
                if not d['@spacecraft'] or not d['@frequency']: continue  # sometimes there is no uplink/downlink

                spacecraft = d['@spacecraft']  # now can build a struct based on spacecraft
                dsn_data.setdefault(d['@spacecraft'], {})
                spacecraft_data = {k[1:]:v for k,v in d.items()}  # just removing the @ signs here

                del(spacecraft_data['spacecraft'])  # redundant here

                dsn_data[spacecraft]['last_upSignal'] = spacecraft_data
                dsn_data[spacecraft]['last_upSignal_station'] = station
                dsn_data[spacecraft]['last_upSignal_dish'] = dish_name
                dsn_data[spacecraft]['last_upSignal_date'] = last_contact

            r_server.set(spacecraft, dsn_data[spacecraft])
            print('dsn database updated')


