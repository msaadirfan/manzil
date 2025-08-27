from collections import defaultdict
from routefinder.models import Station
from routefinder.models import Route
from dijkstras import get_connected_component

def normalize(name: str) -> str: 
    if not name:
        return ""
    return " ".join(name.strip().split()).title()

def transit_map(debug=False):
    graph = defaultdict(dict)
    route_info = defaultdict(dict) 
    routes_per_station = defaultdict(set)  
    routes = Route.objects.select_related("from_station", "to_station")
    
    station_names = set()
    for station in Station.objects.all():
        normalized_name = normalize(station.station_name)
        graph[normalized_name]
        station_names.add(normalized_name)
    
    if debug:
        print(f"Total stations loaded: {len(station_names)}")
    
    
    route_count = 0
    for route in routes:
        from_name = normalize(route.from_station.station_name)
        to_name = normalize(route.to_station.station_name)
        distance = float(route.distance_kms)
        route_id = route.route_id
        
       
        graph[from_name][to_name] = distance
        graph[to_name][from_name] = distance
        
        route_info[from_name][to_name] = route_id
        route_info[to_name][from_name] = route_id
        
        routes_per_station[from_name].add(route_id)
        routes_per_station[to_name].add(route_id)
        
        route_count += 1
    
    if debug:
        print(f"Total routes processed: {route_count}")
        print(f"Graph has {len(graph)} nodes")
    
    return dict(graph), dict(route_info), dict(routes_per_station)


def find_station_by_partial_name(partial_name):
    normalized_partial = normalize(partial_name)
    matches = []
    
    for station in Station.objects.all():
        normalized_station = normalize(station.station_name)
        if normalized_partial.lower() in normalized_station.lower():
            matches.append(normalized_station)
    
    return matches


def validate_graph_connectivity(graph):
    issues = []
    
    isolated = [station for station, connections in graph.items() if not connections]
    if isolated:
        issues.append(f"Isolated stations (no connections): {len(isolated)} stations")
    
    all_stations = set(graph.keys())
    visited_global = set()
    components = []
    
    for station in all_stations:
        if station not in visited_global:
            component = get_connected_component(graph, station)
            components.append(len(component))
            visited_global.update(component)
    
    if len(components) > 1:
        issues.append(f"Graph has {len(components)} disconnected components of sizes: {components}")
    
    return issues

def diagnose_graph_issues():
    print("=== GRAPH DIAGNOSIS ===")
    
    station_count = Station.objects.count()
    route_count = Route.objects.count()
    print(f"Stations in DB: {station_count}")
    print(f"Routes in DB: {route_count}")
    
    if station_count == 0:
        print("ERROR: No stations found in database!")
        return
    
    if route_count == 0:
        print("ERROR: No routes found in database!")
        return
    
    graph = transit_map(debug=True)
    issues = validate_graph_connectivity(graph)
    
    if not issues:
        print("Graph appears to be properly connected!")
    else:
        print("Graph connectivity issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    connected_stations = [s for s, conn in graph.items() if conn]
    if len(connected_stations) >= 2:
        test_source = connected_stations[0]
        test_target = connected_stations[1]
        print(f"\n=== TESTING ROUTE: {test_source} → {test_target} ===")
        cost, path = dijkstra_debug(graph, test_source, test_target, debug=True)
        
        if cost != float("inf"):
            print(f"Test route successful! Distance: {cost}")
        else:
            print("Test route failed!")