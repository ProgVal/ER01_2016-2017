import csv
import json
import networkx

# Expects a graph.json, downloaded with this command:
# wget https://www.fc00.org/static/graph.json

SOURCE_NODE = "fcd6:9c33:dd06:3320:8dbe:ab19:0c87:f6e3" # aka hydrogen.hype.progval.net, the node used to run the pings.

def get_graph():
    with open('graph.json') as f:
        edges = json.load(f)['edges']
    graph = networkx.Graph()
    graph.add_edges_from(
            (edge['sourceID'], edge['targetID'])
            for edge in edges
            )
    return graph

def compute_distances(graph, source):
    return list(networkx.shortest_path_length(graph, SOURCE_NODE).items())

def write_csv(rows):
    with open('node_distances.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(('node', 'distance'))
        for row in rows:
            writer.writerow(row)


write_csv(compute_distances(get_graph(), SOURCE_NODE))
