import re
import csv
import time
import socket
import requests
import subprocess
from multiprocessing.dummy import Pool
from pprint import pprint

# How to use:
# On a server connected to Hyperboria (or any cjdns network), create
# the file “scan_data.csv” with this content:
# timestamp,round_start_timestamp,node,seq,nb_bytes,ttl,latency
#
# Then, run: python3 ping_scan.py and wait for the results.

NB_CONSECUTIVE_PINGS = 3
TIMEOUT = 10

GRAPH_JSON_URL = 'https://www.fc00.org/static/graph.json'
HIA_JSON_URL = 'http://api.hia.cjdns.ca/'

def get_nodes():
    """Return a list of nodes from public databases (fc00 and the HIA)."""
    hia_headers = {'User-Agent': 'test-pings-hyperboria'}
    print('Downloading nodes from HIA.')
    nodes = set()
    nodes = set(requests.get(HIA_JSON_URL, headers=hia_headers).json())
    print('Downloading nodes from fc00')
    nodes.update(node['id'] for node in requests.get(GRAPH_JSON_URL).json()['nodes'])
    print('Done.')
    nodes = {n for n in nodes if socket.inet_pton(socket.AF_INET6, n) and n.startswith('fc')}
    return nodes

ping_re = re.compile(r'\[(?P<timestamp>[0-9.]+)\] (?P<nb_bytes>[0-9]+) bytes from (?P<node>[^ ]+): icmp_seq=(?P<seq>[0-9]+) ttl=(?P<ttl>[0-9]+) time=(?P<latency>.*s)')
def ping_node(node):
    """Run NB_CONSECUTIVE_PINGS pings to a given IPv6."""
    round_start = time.time()
    try:
        output = subprocess.check_output(['ping', node, '-c', str(NB_CONSECUTIVE_PINGS), '-W', str(TIMEOUT), '-D', '-n'], timeout=TIMEOUT+2)
        output = output.decode()
    except:
        output = ''
    print('got one node.')
    results = [('NA', round_start, node, seq, 'NA', 'NA', 'NA')
            for seq in range(NB_CONSECUTIVE_PINGS)]
    matches = ping_re.finditer(output)
    for match in matches:
        seq = int(match.group('seq'))
        results[seq-1] = (match.group('timestamp'), round_start, node, seq+1, match.group('nb_bytes'), match.group('ttl'), match.group('latency'))
    return results




with Pool(100) as pool:
    with open('scan_data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        while True:
            threads = []
            nodes = get_nodes()
            round_start = time.time()
            all_results = pool.map(ping_node, nodes)
            #all_results = pool.map(ping_node, list(nodes)[0:5])
            for writer_results in all_results:
                for result in writer_results:
                    writer.writerow(result)
            csvfile.flush()
            print('Round done.')

            # No more than one round per 10 minutes
            while round_start + 10*60 > time.time():
                time.sleep(1)
