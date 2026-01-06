from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime
from django.contrib import messages
from routefinder.models import Contact, Contribute, Report
from dijkstras import dijkstra, analyze_route_path
from transit import transit_map, normalize, find_station_by_partial_name, validate_graph_connectivity
from .models import Station
from .models import Route
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


# Create your views here.
def index(request):
    return render(request, 'index.html')

def routes(request):
    return render(request, 'routes.html')


def contact(request):
    """Report Management Page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        report_type = request.POST.get('report_type')
        description = request.POST.get('desc')
        
        if not all([name, email, report_type, description]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'contact.html')
        
        #Create the report
        report = Report(
            name=name,
            email=email,
            report_type=report_type,
            description=description
        )
        report.save()
        
        #Different messages based on priority
        if report_type == 'harassment':
            messages.success(request, "⚠️ URGENT: Your harassment report has been submitted with CRITICAL priority. Our team will address this immediately.")
        elif report_type == 'safety_hazard':
            messages.success(request, "⚠️ Your safety hazard report has been submitted with HIGH priority. We will investigate promptly.")
        else:
            messages.success(request, "✓ Your report has been submitted successfully. We'll review it soon.")
        
        return redirect('contact')
    
    return render(request, 'contact.html')


@staff_member_required
def admin_reports(request):
    """Admin view to see all reports in priority order"""
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        action = request.POST.get('action')
        
        try:
            report = Report.objects.get(id=report_id)
            
            if action == 'resolve':
                report.is_resolved = True
                report.resolved_date = datetime.now()
                report.admin_notes = request.POST.get('admin_notes', '')
                report.save()
                messages.success(request, f"Report #{report_id} marked as resolved.")
            elif action == 'delete':
                report.delete()
                messages.success(request, f"Report #{report_id} deleted.")
                
        except Report.DoesNotExist:
            messages.error(request, "Report not found.")
        
        return redirect('admin_reports')
    
    #Get reports separated by status
    pending_reports = Report.objects.filter(is_resolved=False).order_by('priority_level', '-date')
    resolved_reports = Report.objects.filter(is_resolved=True).order_by('-resolved_date')[:20]
    
    #Stats/dashboard
    total_reports = Report.objects.count()
    pending_count = pending_reports.count()
    critical_count = Report.objects.filter(is_resolved=False, priority_level=1).count()
    high_priority_count = Report.objects.filter(is_resolved=False, priority_level=2).count()
    
    context = {
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'total_reports': total_reports,
        'pending_count': pending_count,
        'critical_count': critical_count,
        'high_priority_count': high_priority_count,
    }
    
    return render(request, 'admin_reports.html', context)
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
           
            print("Building transit map with routes")
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


#admin login

def admin_login(request):
    #login page for admin
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_reports')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('admin_reports')
            else:
                messages.error(request, "You don't have permission to access the admin panel.")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'admin_login.html')


def admin_logout(request):
    """Logout view for admin"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('admin_login')


@login_required(login_url='admin_login')
def admin_reports(request):
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        action = request.POST.get('action')
        
        try:
            report = Report.objects.get(id=report_id)
            
            if action == 'resolve':
                report.is_resolved = True
                report.resolved_date = datetime.now()
                report.admin_notes = request.POST.get('admin_notes', '')
                report.save()
                messages.success(request, f"Report #{report_id} marked as resolved.")
            elif action == 'delete':
                report.delete()
                messages.success(request, f"Report #{report_id} deleted.")
                
        except Report.DoesNotExist:
            messages.error(request, "Report not found.")
        
        return redirect('admin_reports')
    
    # Get reports separated by status
    pending_reports = Report.objects.filter(is_resolved=False).order_by('priority_level', '-date')
    resolved_reports = Report.objects.filter(is_resolved=True).order_by('-resolved_date')[:20]
    
    #Stats
    total_reports = Report.objects.count()
    pending_count = pending_reports.count()
    critical_count = Report.objects.filter(is_resolved=False, priority_level=1).count()
    high_priority_count = Report.objects.filter(is_resolved=False, priority_level=2).count()
    
    context = {
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'total_reports': total_reports,
        'pending_count': pending_count,
        'critical_count': critical_count,
        'high_priority_count': high_priority_count,
        'admin_user': request.user,
    }
    
    return render(request, 'admin_reports.html', context)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
@require_http_methods(["GET"])
def api_stations(request):
    """API endpoint to get all stations with coordinates from database"""
    stations = Station.objects.all()
    
    data = []
    for station in stations:
        # Only include stations that have coordinates
        if station.lat and station.lng:  # Changed from latitude/longitude
            data.append({
                'station_id': station.station_id,
                'station_name': station.station_name,
                'lat': float(station.lat),          # Changed
                'lng': float(station.lng)           # Changed
            })
    
    print(f"API: Returning {len(data)} stations with coordinates")
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def api_routes(request):
    """API endpoint to get all route segments"""
    routes = Route.objects.select_related('from_station', 'to_station').all()
    
    data = []
    for route in routes:
        # Only include routes where both stations have coordinates
        if (route.from_station.lat and route.from_station.lng and  # Changed
            route.to_station.lat and route.to_station.lng):        # Changed
            
            data.append({
                'route_id': route.route_id,
                'from_station_id': route.from_station.station_id,
                'to_station_id': route.to_station.station_id,
                'from_lat': float(route.from_station.lat),         # Changed
                'from_lng': float(route.from_station.lng),         # Changed
                'to_lat': float(route.to_station.lat),             # Changed
                'to_lng': float(route.to_station.lng)              # Changed
            })
    
    print(f"API: Returning {len(data)} route segments")
    return JsonResponse(data, safe=False)

def map_view(request):
    """Render the map page"""
    return render(request, 'map.html')