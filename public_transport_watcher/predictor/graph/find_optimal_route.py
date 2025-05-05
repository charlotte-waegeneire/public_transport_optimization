import networkx as nx


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
    # Verify that the start and end stations exist in the graph
    if start_station_id not in G:
        print(f"Start station {start_station_id} not found in network")
        return None, float("inf"), {"error": f"Start station {start_station_id} not found in network"}

    if end_station_id not in G:
        print(f"End station {end_station_id} not found in network")
        return None, float("inf"), {"error": f"End station {end_station_id} not found in network"}

    # Create an extended graph to explicitly handle transfers
    # This approach uses a modified version of the network where each node
    # is split into multiple nodes - one for each transport line serving it
    extended_G = nx.DiGraph()

    # Step 1: Create transport-specific nodes for each station
    transport_at_station = {}
    for u, v, data in G.edges(data=True):
        transport_id = data.get("transport_id")
        # Track which transports serve each station
        if u not in transport_at_station:
            transport_at_station[u] = set()
        transport_at_station[u].add(transport_id)

    # Step 2: Create nodes in extended graph
    for node_id in G.nodes():
        # Get station attributes
        node_attrs = G.nodes[node_id]

        if node_id in transport_at_station:
            # Create a node for each transport line at this station
            for transport_id in transport_at_station[node_id]:
                extended_node_id = (node_id, transport_id)
                extended_G.add_node(extended_node_id, **node_attrs, original_id=node_id)

            # Create transfer edges between different transport lines at the same station
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
            # For stations with no outgoing transports, just add them as is
            extended_G.add_node(node_id, **node_attrs, original_id=node_id)

    # Step 3: Add travel edges from the original graph
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

    # Step 4: Handle special cases for start and end stations
    # If start station has multiple transports, we need to be able to start with any of them
    start_node_extended = None
    if start_station_id in transport_at_station:
        # Create a virtual start node
        start_node_extended = f"start_{start_station_id}"
        extended_G.add_node(
            start_node_extended, name=f"Start at {G.nodes[start_station_id].get('name', start_station_id)}"
        )

        # Connect to all transport options at the starting station with zero weight
        for transport_id in transport_at_station[start_station_id]:
            extended_G.add_edge(
                start_node_extended,
                (start_station_id, transport_id),
                weight=0,
                original_edge=False,
                is_transfer=False,
                transport_id="Start",
            )
    else:
        start_node_extended = start_station_id

    # If end station has multiple transports, we need to be able to end with any of them
    end_node_extended = None
    if end_station_id in transport_at_station:
        # Create a virtual end node
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
    else:
        end_node_extended = end_station_id

    # Step 5: Find shortest path in the extended graph
    try:
        # Use Dijkstra's algorithm to find the shortest path
        path_extended = nx.dijkstra_path(extended_G, start_node_extended, end_node_extended, weight="weight")
        path_length = nx.dijkstra_path_length(extended_G, start_node_extended, end_node_extended, weight="weight")

        # Step 6: Convert back to original graph nodes
        path = []
        for node in path_extended:
            if isinstance(node, tuple):
                # It's a transport-specific node, get the original station ID
                path.append(node[0])
            elif node.startswith("start_") or node.startswith("end_"):
                # Skip virtual start/end nodes
                continue
            else:
                # It's already an original node
                path.append(node)

        # Remove consecutive duplicates in the path
        path = [path[i] for i in range(len(path)) if i == 0 or path[i] != path[i - 1]]

        # Step 7: Prepare detailed route information
        route_info = {
            "station_names": [G.nodes[station].get("name", f"Station {station}") for station in path],
            "num_stations": len(path),
            "travel_time_mins": path_length,
            "travel_time_formatted": f"{int(path_length // 60)}h {int(path_length % 60)}min"
            if path_length >= 60
            else f"{int(path_length)}min",
            "segments": [],
        }

        # Get information about each segment of the journey
        current_transport = None
        num_transfers = 0

        for i in range(len(path_extended) - 1):
            from_node = path_extended[i]
            to_node = path_extended[i + 1]

            # Skip virtual start/end nodes in segment analysis
            if isinstance(from_node, str) and (from_node.startswith("start_") or from_node.startswith("end_")):
                continue
            if isinstance(to_node, str) and (to_node.startswith("start_") or to_node.startswith("end_")):
                continue

            # Get edge data
            edge_data = extended_G[from_node][to_node]

            # Extract original station IDs
            from_station = from_node[0] if isinstance(from_node, tuple) else from_node
            to_station = to_node[0] if isinstance(to_node, tuple) else to_node

            # Only add segment if stations are different (to avoid transfers at same station)
            if from_station != to_station:
                transport_id = edge_data.get("transport_id")
                travel_time = edge_data.get("weight", 5.0)

                # Check if this is a transfer (we're on different transport than before)
                is_transfer = (
                    current_transport is not None and transport_id != current_transport and transport_id != "End"
                )

                if is_transfer:
                    num_transfers += 1

                # Only update current transport if it's not a special marker
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

        # Set the number of transfers
        route_info["num_transfers"] = num_transfers

        return path, path_length, route_info

    except nx.NetworkXNoPath:
        print(f"No path found between {start_station_id} and {end_station_id}")
        return None, float("inf"), {"error": "No path found"}
    except Exception as e:
        print(f"Error finding route: {str(e)}")
        return None, float("inf"), {"error": f"Error finding route: {str(e)}"}
