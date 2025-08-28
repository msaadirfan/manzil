from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime
from django.contrib import messages
from routefinder.models import Contact, Contribute
from dijkstras import dijkstra, analyze_route_path
from transit import transit_map, normalize, find_station_by_partial_name, validate_graph_connectivity
from .models import Station
from .models import Route
from django_ratelimit.decorators import ratelimit

# Create your views here.
def index(request):
    return render(request, 'index.html')

def routes(request):
    return render(request, 'routes.html')


def contact(request):
    if request.method=='POST':
        name=request.POST.get('name')
        email=request.POST.get('email')
        desc=request.POST.get('desc')
        contact=Contact(name=name, email=email, desc=desc, date= datetime.today())
        contact.save()
        messages.success(request,"Message saved. Thanks for contacting us.")

    return render(request,'contact.html')

def contribute(request):
    if request.method=='POST':
        name=request.POST.get('name')
        email=request.POST.get('email')
        desc=request.POST.get('desc')
        contribute=Contribute(name=name, email=email, desc=desc, date=datetime.today())
        contribute.save()
        messages.success(request, "Thank you for the contribution.")
    return render(request,'contribute.html')

def home(request):
    return render(request,'home.html')

def map(request):
    return render(request,'map.html')

def station_search(request):
    query = request.GET.get("q", "")
    if query:
        stations = Station.objects.filter(station_name__icontains=query)[:10]
    else:
        stations = Station.objects.all()[:10]

    results = [s.station_name for s in stations]
    return JsonResponse(results, safe=False)

def find_route(request):
    if request.method == "POST":
        from django.contrib import messages
        from django.shortcuts import render
        
        from_station_raw = request.POST.get("fromStation", "").strip()
        to_station_raw = request.POST.get("toStation", "").strip()
        
        if not from_station_raw or not to_station_raw:
            messages.error(request, "Please enter both start and destination stations.")
            return render(request, "home.html")
        
        from_station = normalize(from_station_raw)
        to_station = normalize(to_station_raw)
        
        if from_station == to_station:
            messages.error(request, "Please select different stations.")
            return render(request, "home.html")
        
        try:
           
            print("Building transit map with routes...")
            graph, route_info, routes_per_station = transit_map(debug=True)
            
            print(f"\nSearching from '{from_station}' to '{to_station}'")
            
           
            if from_station not in graph:
                messages.error(request, f"Start station '{from_station_raw}' not found.")
                return render(request, "home.html")
            
            if to_station not in graph:
                messages.error(request, f"Destination station '{to_station_raw}' not found.")
                return render(request, "home.html")
            
            cost, path_with_routes = dijkstra(graph, route_info, from_station, to_station, debug=True)
            
            if cost == float("inf"):
                messages.error(request, f"No route found between {from_station} and {to_station}.")
                return render(request, "home.html")
            
            route_segments = analyze_route_path(path_with_routes)
            
            num_transfers = max(0, len(route_segments) - 1)
            
            simple_path = [station_info['station'] for station_info in path_with_routes]
            avg_speed_of_bus=26
            travel_time=(cost/avg_speed_of_bus)*60
            return render(
                request,
                "routes.html",
                {
                    "from_station": from_station,
                    "to_station": to_station,
                    "path": simple_path,  
                    "path_with_routes": path_with_routes,
                    "route_segments": route_segments,
                    "total_distance": round(cost, 2),
                    "num_stations": len(simple_path),
                    "num_transfers": num_transfers,
                    "travel_time":round(travel_time),
                    "routes_used": [seg['route_id'] for seg in route_segments]
                },
            )
            
        except Exception as e:
            print(f"Error in route finding: {str(e)}")
            messages.error(request, f"An error occurred while finding the route: {str(e)}")
            return render(request, "home.html")



@ratelimit(key='ip', rate='5/m', block=True)
def contact_view(request):
    message.error(request, f"Too many requests are being sent, limit reached.")
    return render(request, "home.html")
