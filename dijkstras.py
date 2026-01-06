import heapq

#transfer penalty in kilometers(equivalent to 5-10 minutes of travel time)
TRANSFER_PENALTY = 5.0

def dijkstra(transit_map, route_info, source_node, target_node, debug=False):
    
    if source_node not in transit_map:
        available_stations = list(transit_map.keys())[:10]
        raise ValueError(f"Source station '{source_node}' not found in graph. "
                        f"Available stations include: {available_stations}")
    
    if target_node not in transit_map:
        available_stations = list(transit_map.keys())[:10]
        raise ValueError(f"Target station '{target_node}' not found in graph. "
                        f"Available stations include: {available_stations}")
    
    if debug:
        print(f"\n=== DIJKSTRA WITH ROUTES DEBUG ===")
        print(f"Source: '{source_node}'")
        print(f"Target: '{target_node}'")
        print(f"Transfer penalty: {TRANSFER_PENALTY} km")
    
    # Priority queue: (cost, counter, node, path, current_route)
    # Start with NO route (none) so we can pick the best first route
    queue = [(0, 0, source_node, [{'station': source_node, 'route': None, 'is_transfer': False}], None)]
    
    # Track best cost to reach each (station, route) pair
    # Key: (station, route), Value: cost
    seen = {}
    iterations = 0
    counter = 1  # Unique counter for tiebreaking
    
    while queue:
        iterations += 1
        (cost, _, node, path, current_route) = heapq.heappop(queue)
        
        if debug and iterations <= 15:
            print(f"Iteration {iterations}: Processing '{node}' | Cost: {cost:.2f} | Route: {current_route}")
        
        # Use (node, route) as state key to allow revisiting stations on different routes
        state = (node, current_route)
        
        # Skip if we've seen this state with lower or equal cost
        if state in seen and seen[state] <= cost:
            continue
            
        seen[state] = cost
        
        # Check if we've reached the target
        if node == target_node:
            if debug:
                print(f"\n=== PATH FOUND ===")
                print(f"Total cost: {cost:.2f} km")
                print(f"Path length: {len(path)} stations")
                
                # Count transfers
                transfers = sum(1 for p in path if p.get('is_transfer', False))
                print(f"Number of transfers: {transfers}")
            return (cost, path)
        
        neighbors = transit_map.get(node, {})
        
        for neighbor, distance in neighbors.items():
            # Get ALL routes for this edge (now a list)
            available_routes = route_info.get(node, {}).get(neighbor, [])
            
            if not available_routes:
                continue  # Skip if no route info
            
            # Try each available route
            for next_route in available_routes:
                # Determine if this is a transfer
                # If current_route is None (starting point), it's NOT a transfer
                is_transfer = False
                if current_route is not None and current_route != next_route:
                    is_transfer = True
                
                # Calculate actual cost including transfer penalty
                edge_cost = distance
                if is_transfer:
                    edge_cost += TRANSFER_PENALTY
                    
                    if debug and iterations <= 15:
                        print(f"  → Transfer at '{node}': {current_route} → {next_route} (penalty: +{TRANSFER_PENALTY} km)")
                
                # Create new path entry
                new_path_entry = {
                    'station': neighbor,
                    'route': next_route,
                    'is_transfer': is_transfer,
                    'distance_from_prev': distance,  # Store actual distance, not penalized
                    'transfer_penalty': TRANSFER_PENALTY if is_transfer else 0
                }
                
                new_path = path + [new_path_entry]
                new_cost = cost + edge_cost
                
                # Check if this path to (neighbor, next_route) is better
                next_state = (neighbor, next_route)
                if next_state not in seen or seen[next_state] > new_cost:
                    heapq.heappush(queue, (new_cost, counter, neighbor, new_path, next_route))
                    counter += 1
    
    if debug:
        print(f"\n=== NO PATH FOUND ===")
        print(f"Iterations completed: {iterations}")
    
    return (float("inf"), [])


def analyze_route_path(path_with_routes):
    """
    Analyzes a path and groups consecutive stations on the same route into segments.
    """
    if not path_with_routes or len(path_with_routes) < 2:
        return []
    
    segments = []
    current_segment = {
        'route_id': None,
        'stations': [],
        'distance': 0,
        'start_station': None,
        'end_station': None
    }
    
    # Skip the first station (it has route: None)
    first_station = path_with_routes[0]
    
    for i, station_info in enumerate(path_with_routes[1:], 1):
        route_id = station_info['route']
        station_name = station_info['station']
        distance = station_info.get('distance_from_prev', 0)
        
        if current_segment['route_id'] is None:
            # Start first segment
            current_segment['route_id'] = route_id
            current_segment['stations'] = [path_with_routes[0]['station']]
            current_segment['start_station'] = path_with_routes[0]['station']
        
        if route_id == current_segment['route_id']:
            # Continue current segment
            current_segment['stations'].append(station_name)
            current_segment['distance'] += distance
            current_segment['end_station'] = station_name
        else:
            # Route changed - save current segment and start new one
            segments.append(current_segment.copy())
            current_segment = {
                'route_id': route_id,
                'stations': [path_with_routes[i-1]['station'], station_name],
                'distance': distance,
                'start_station': path_with_routes[i-1]['station'],
                'end_station': station_name
            }
    
    # Don't forget the last segment
    if current_segment['stations']:
        segments.append(current_segment)
    
    return segments


def get_connected_component(graph, start_node):
    """
    Returns all nodes reachable from start_node via BFS.
    """
    visited = set()
    queue = [start_node]
    
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        
        for neighbor in graph.get(node, {}):
            if neighbor not in visited:
                queue.append(neighbor)
    
    return visited