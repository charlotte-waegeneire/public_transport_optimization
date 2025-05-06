import networkx as nx

from public_transport_watcher.logging_config import get_logger

logger = get_logger()


def _validate_stations(G, start_station_id, end_station_id):
    if start_station_id not in G:
        error_message = {"error": f"Start station {start_station_id} not found in network"}
        logger.error(error_message["error"])
        return False, error_message

    if end_station_id not in G:
        error_message = {"error": f"End station {end_station_id} not found in network"}
        logger.error(error_message["error"])
        return False, error_message

    return True, {}


def _map_transport_to_stations(G):
    transport_at_station = {}
    for u, v, data in G.edges(data=True):
        transport_id = data.get("transport_id")
        if u not in transport_at_station:
            transport_at_station[u] = set()
        transport_at_station[u].add(transport_id)

    return transport_at_station


def _create_extended_graph_nodes(G, transport_at_station, transfer_penalty):
    extended_G = nx.DiGraph()

    for node_id in G.nodes():
        node_attrs = G.nodes[node_id]

        if node_id in transport_at_station:
            for transport_id in transport_at_station[node_id]:
                extended_node_id = (node_id, transport_id)
                extended_G.add_node(extended_node_id, **node_attrs, original_id=node_id)

            transports = list(transport_at_station[node_id])
            for i in range(len(transports)):
                for j in range(len(transports)):
                    if i != j:  # Different transport lines
                        from_transport = transports[i]
                        to_transport = transports[j]
                        # Add transfer edge with penalty
                        extended_G.add_edge(
                            (node_id, from_transport),
                            (node_id, to_transport),
                            weight=transfer_penalty,
                            original_edge=False,
                            is_transfer=True,
                            transport_id="Transfer",
                        )
        else:
            extended_G.add_node(node_id, **node_attrs, original_id=node_id)

    return extended_G


def _add_travel_edges(G, extended_G, transport_at_station):
    for u, v, data in G.edges(data=True):
        transport_id = data.get("transport_id")

        # Only add edge if both stations are served by this transport
        if u in transport_at_station and transport_id in transport_at_station[u]:
            if v in transport_at_station and transport_id in transport_at_station[v]:
                # Add edge between the transport-specific nodes
                extended_G.add_edge((u, transport_id), (v, transport_id), **data, original_edge=True, is_transfer=False)
            elif v not in transport_at_station:
                # Handle case where destination has no outgoing edges
                extended_G.add_edge((u, transport_id), v, **data, original_edge=True, is_transfer=False)


def _handle_start_station(G, extended_G, start_station_id, transport_at_station):
    if start_station_id in transport_at_station:
        start_node_extended = f"start_{start_station_id}"
        extended_G.add_node(
            start_node_extended, name=f"Start at {G.nodes[start_station_id].get('name', start_station_id)}"
        )

        for transport_id in transport_at_station[start_station_id]:
            extended_G.add_edge(
                start_node_extended,
                (start_station_id, transport_id),
                weight=0,
                original_edge=False,
                is_transfer=False,
                transport_id="Start",
            )
        return start_node_extended
    else:
        return start_station_id


def _handle_end_station(G, extended_G, end_station_id, transport_at_station):
    if end_station_id in transport_at_station:
        end_node_extended = f"end_{end_station_id}"
        extended_G.add_node(end_node_extended, name=f"End at {G.nodes[end_station_id].get('name', end_station_id)}")

        # Connect from all transport options at the ending station with zero weight
        for transport_id in transport_at_station[end_station_id]:
            extended_G.add_edge(
                (end_station_id, transport_id),
                end_node_extended,
                weight=0,
                original_edge=False,
                is_transfer=False,
                transport_id="End",
            )
        return end_node_extended
    else:
        return end_station_id


def _convert_extended_path_to_original(path_extended):
    path = []
    for node in path_extended:
        if isinstance(node, tuple):
            path.append(node[0])
        elif isinstance(node, str) and (node.startswith("start_") or node.startswith("end_")):
            continue
        else:
            path.append(node)

    path = [path[i] for i in range(len(path)) if i == 0 or path[i] != path[i - 1]]

    return path


def _create_route_info(G, path, path_extended, extended_G, path_length):
    route_info = {
        "station_names": [G.nodes[station].get("name", f"Station {station}") for station in path],
        "num_stations": len(path),
        "travel_time_mins": path_length,
        "travel_time_formatted": f"{int(path_length // 60)}h {int(path_length % 60)}min"
        if path_length >= 60
        else f"{int(path_length)}min",
        "segments": [],
    }

    current_transport = None
    num_transfers = 0

    for i in range(len(path_extended) - 1):
        from_node = path_extended[i]
        to_node = path_extended[i + 1]

        if isinstance(from_node, str) and (from_node.startswith("start_") or from_node.startswith("end_")):
            continue
        if isinstance(to_node, str) and (to_node.startswith("start_") or to_node.startswith("end_")):
            continue

        edge_data = extended_G[from_node][to_node]

        from_station = from_node[0] if isinstance(from_node, tuple) else from_node
        to_station = to_node[0] if isinstance(to_node, tuple) else to_node

        if from_station != to_station:
            transport_id = edge_data.get("transport_id")
            travel_time = edge_data.get("weight", 5.0)

            is_transfer = current_transport is not None and transport_id != current_transport and transport_id != "End"

            if is_transfer:
                num_transfers += 1

            if transport_id not in ["Start", "End", "Transfer"]:
                current_transport = transport_id

            segment = {
                "from_station_id": from_station,
                "from_station_name": G.nodes[from_station].get("name", f"Station {from_station}"),
                "to_station_id": to_station,
                "to_station_name": G.nodes[to_station].get("name", f"Station {to_station}"),
                "transport_id": transport_id,
                "travel_time_mins": travel_time,
                "is_transfer": is_transfer,
            }

            route_info["segments"].append(segment)

    route_info["num_transfers"] = num_transfers

    return route_info


def find_optimal_route(G, start_station_id, end_station_id, transfer_penalty=5.0):
    """
    Find the optimal route between two stations with proper handling of transfer penalties

    Parameters:
    -----------
    G : networkx.DiGraph
        The transport network graph
    start_station_id : int
        ID of the starting station
    end_station_id : int
        ID of the destination station
    transfer_penalty : float
        Additional time (in minutes) to add for transfers

    Returns:
    --------
    list
        List of station IDs representing the optimal path
    float
        Total travel time/weight of the path (in minutes)
    dict
        Additional information about the route (stations names, transfers, etc.)
    """
    valid, error = _validate_stations(G, start_station_id, end_station_id)
    if not valid:
        return None, float("inf"), error

    transport_at_station = _map_transport_to_stations(G)

    extended_G = _create_extended_graph_nodes(G, transport_at_station, transfer_penalty)
    _add_travel_edges(G, extended_G, transport_at_station)

    start_node_extended = _handle_start_station(G, extended_G, start_station_id, transport_at_station)
    end_node_extended = _handle_end_station(G, extended_G, end_station_id, transport_at_station)

    try:
        path_extended = nx.dijkstra_path(extended_G, start_node_extended, end_node_extended, weight="weight")
        path_length = nx.dijkstra_path_length(extended_G, start_node_extended, end_node_extended, weight="weight")

        path = _convert_extended_path_to_original(path_extended)

        route_info = _create_route_info(G, path, path_extended, extended_G, path_length)

        return path, path_length, route_info

    except nx.NetworkXNoPath:
        logger.error(f"No path found between {start_station_id} and {end_station_id}")
        return None, float("inf"), {"error": "No path found"}
    except Exception as e:
        logger.error(f"Error finding route: {str(e)}")
        return None, float("inf"), {"error": f"Error finding route: {str(e)}"}
