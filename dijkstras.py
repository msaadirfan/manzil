import heapq

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
    
    
    queue = [(0, source_node, [{'station': source_node, 'route': None, 'is_transfer': False}], None)]
    seen = set()
    iterations = 0
    
    while queue:
        iterations += 1
        (cost, node, path, current_route) = heapq.heappop(queue)
        
        if debug and iterations <= 5:
            print(f"Iteration {iterations}: Processing node '{node}' with cost {cost}, current route: {current_route}")
        
        if node in seen:
            continue
            
        seen.add(node)
        
        if node == target_node:
            if debug:
                print(f"=== PATH FOUND WITH ROUTES ===")
                print(f"Total cost: {cost}")
                print(f"Path length: {len(path)} stations")
            return (cost, path)
        
        neighbors = transit_map.get(node, {})
        
        for neighbor, weight in neighbors.items():
            if neighbor not in seen:
              
                next_route = route_info.get(node, {}).get(neighbor)
                
              
                is_transfer = current_route is not None and current_route != next_route
                
                
                new_path_entry = {
                    'station': neighbor,
                    'route': next_route,
                    'is_transfer': is_transfer,
                    'distance_from_prev': weight
                }
                
                new_path = path + [new_path_entry]
                heapq.heappush(queue, (cost + weight, neighbor, new_path, next_route))
    
    if debug:
        print(f"=== NO PATH FOUND ===")
        print(f"Iterations completed: {iterations}")
    
    return (float("inf"), [])

def analyze_route_path(path_with_routes):
    
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
    
    
    first_station = path_with_routes[0]
    
    for i, station_info in enumerate(path_with_routes[1:], 1):
        route_id = station_info['route']
        station_name = station_info['station']
        distance = station_info.get('distance_from_prev', 0)
        
        if current_segment['route_id'] is None:
            
            current_segment['route_id'] = route_id
            current_segment['stations'] = [path_with_routes[0]['station']]
            current_segment['start_station'] = path_with_routes[0]['station']
        
        if route_id == current_segment['route_id']:
            current_segment['stations'].append(station_name)
            current_segment['distance'] += distance
            current_segment['end_station'] = station_name
        else:
            segments.append(current_segment.copy())
            current_segment = {
                'route_id': route_id,
                'stations': [path_with_routes[i-1]['station'], station_name],
                'distance': distance,
                'start_station': path_with_routes[i-1]['station'],
                'end_station': station_name
            }
    
    if current_segment['stations']:
        segments.append(current_segment)
    
    return segments


def get_connected_component(graph, start_node):
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
