import os
import pickle
import redis
from __future__ import print_function
import wolframalpha  # https://pypi.python.org/pypi/wolframalpha

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r_server = redis.StrictRedis.from_url(REDIS_URL)

client = wolframalpha.Client(APP_ID)

# get list of space probes
fname = 'list_active_probes.txt'
probe_names = []
with open(fname) as f:
    content = f.readlines()
    for l in content[1:]:  # first line is a comment
        probe_names.append(l.strip())

# lookup in wolframalpha each probe
probe_data = {}
for probe in probe_names:

    probe_data[probe] = {}
    lookup_str = probe + 'spacecraft'
    print('looking up: ' + lookup_str)
    res = client.query(lookup_str)


    for pod in res.pods[1:]:  # the first one is funky version of spacecraft name
        if not pod.text:
            continue

        data_chunk = pod.text

        for line in data_chunk.split("\n"):
            attr = line.split('|')[0].strip()
            value = [l.strip() for l in line.split('|')[1:]]
            if len(value) == 1:
                value = value[0]
            if value:
                probe_data[probe][attr] = value

# now put them in redis
for name, data in probe_data.items():
    key_name = '_'.join(name.split(' '))  # replace spaces with underscores
    r_server.set(key_name, pickle.dumps(data))
