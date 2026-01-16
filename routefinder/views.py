from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from datetime import datetime
from django.contrib import messages
from routefinder.models import Contact, Contribute, Report, Station, Route
from dijkstras import dijkstra, analyze_route_path
from transit import transit_map, normalize
from django_ratelimit.decorators import ratelimit
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re


# Input sanitization helper
def sanitize_input(text, max_length=200):
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ""
    # Remove any HTML tags
    text = re.sub(r'<[^>]*>', '', str(text))
    # Limit length
    text = text[:max_length]
    # Strip whitespace
    return text.strip()


def index(request):
    return render(request, 'index.html')


def routes(request):
    return render(request, 'routes.html')


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@csrf_protect
def contact(request):
    """Report Management Page with rate limiting and validation"""
    if request.method == 'POST':
        # Sanitize inputs
        name = sanitize_input(request.POST.get('name', ''), 100)
        email = sanitize_input(request.POST.get('email', ''), 150)
        report_type = request.POST.get('report_type', '')
        description = sanitize_input(request.POST.get('desc', ''), 5000)
        
        # Validation
        if not all([name, email, report_type, description]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'contact.html')
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, 'contact.html')
        
        # Validate report type
        valid_types = ['harassment', 'safety_hazard', 'staff_behaviour', 'cleanliness', 'other']
        if report_type not in valid_types:
            messages.error(request, "Invalid report type.")
            return render(request, 'contact.html')
        
        # Create the report
        try:
            report = Report(
                name=name,
                email=email,
                report_type=report_type,
                description=description
            )
            report.save()
            
            # Different messages based on priority
            if report_type == 'harassment':
                messages.success(request, "⚠️ URGENT: Your harassment report has been submitted with CRITICAL priority.")
            elif report_type == 'safety_hazard':
                messages.success(request, "⚠️ Your safety hazard report has been submitted with HIGH priority.")
            else:
                messages.success(request, "✓ Your report has been submitted successfully.")
            
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            # Log the error in production
            import logging
            logging.error(f"Error saving report: {str(e)}")
        
        return redirect('contact')
    
    return render(request, 'contact.html')


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@csrf_protect
def contribute(request):
    """Contribution form with rate limiting and validation"""
    if request.method == 'POST':
        # Sanitize inputs
        name = sanitize_input(request.POST.get('name', ''), 100)
        email = sanitize_input(request.POST.get('email', ''), 150)
        desc = sanitize_input(request.POST.get('desc', ''), 5000)
        
        # Validation
        if not all([name, email, desc]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'contribute.html')
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, 'contribute.html')
        
        try:
            contribute = Contribute(
                name=name,
                email=email,
                desc=desc,
                date=datetime.today()
            )
            contribute.save()
            messages.success(request, "Thank you for the contribution.")
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            import logging
            logging.error(f"Error saving contribution: {str(e)}")
        
        return redirect('contribute')
    
    return render(request, 'contribute.html')


def home(request):
    return render(request, 'home.html')


def map(request):
    return render(request, 'map.html')


@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def station_search(request):
    """Station search with rate limiting"""
    query = sanitize_input(request.GET.get("q", ""), 100)
    
    if query:
        # Use parameterized query to prevent SQL injection
        stations = Station.objects.filter(station_name__icontains=query)[:10]
    else:
        stations = Station.objects.all()[:10]

    results = [s.station_name for s in stations]
    return JsonResponse(results, safe=False)


@ratelimit(key='ip', rate='20/m', method='POST', block=True)
@csrf_protect
def find_route(request):
    """Route finder with rate limiting and validation"""
    if request.method == "POST":
        # Sanitize inputs
        from_station_raw = sanitize_input(request.POST.get("fromStation", ""), 200)
        to_station_raw = sanitize_input(request.POST.get("toStation", ""), 200)
        
        if not from_station_raw or not to_station_raw:
            messages.error(request, "Please enter both start and destination stations.")
            return render(request, "home.html")
        
        from_station = normalize(from_station_raw)
        to_station = normalize(to_station_raw)
        
        if from_station == to_station:
            messages.error(request, "Please select different stations.")
            return render(request, "home.html")
        
        try:
            graph, route_info, routes_per_station = transit_map(debug=False)
            
            # Validate stations exist
            if from_station not in graph:
                messages.error(request, f"Start station '{from_station_raw}' not found.")
                return render(request, "home.html")
            
            if to_station not in graph:
                messages.error(request, f"Destination station '{to_station_raw}' not found.")
                return render(request, "home.html")
            
            cost, path_with_routes = dijkstra(graph, route_info, from_station, to_station, debug=False)
            
            if cost == float("inf"):
                messages.error(request, f"No route found between {from_station} and {to_station}.")
                return render(request, "home.html")
            
            route_segments = analyze_route_path(path_with_routes)
            num_transfers = max(0, len(route_segments) - 1)
            simple_path = [station_info['station'] for station_info in path_with_routes]
            avg_speed_of_bus = 26
            travel_time = (cost / avg_speed_of_bus) * 60
            
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
                    "travel_time": round(travel_time),
                    "routes_used": [seg['route_id'] for seg in route_segments]
                },
            )
            
        except Exception as e:
            messages.error(request, "An error occurred while finding the route.")
            import logging
            logging.error(f"Error in route finding: {str(e)}")
            return render(request, "home.html")
    
    return render(request, "home.html")


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@csrf_protect
def admin_login(request):
    """Admin login with rate limiting"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_reports')
    
    if request.method == 'POST':
        username = sanitize_input(request.POST.get('username', ''), 150)
        password = request.POST.get('password', '')  # Don't sanitize passwords
        
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'admin_login.html')
        
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
@staff_member_required
def admin_reports(request):
    """Admin reports view with proper authentication"""
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        action = request.POST.get('action')
        
        try:
            report = Report.objects.get(id=report_id)
            
            if action == 'resolve':
                report.is_resolved = True
                report.resolved_date = datetime.now()
                report.admin_notes = sanitize_input(request.POST.get('admin_notes', ''), 1000)
                report.save()
                messages.success(request, f"Report #{report_id} marked as resolved.")
            elif action == 'delete':
                report.delete()
                messages.success(request, f"Report #{report_id} deleted.")
                
        except Report.DoesNotExist:
            messages.error(request, "Report not found.")
        except Exception as e:
            messages.error(request, "An error occurred.")
            import logging
            logging.error(f"Error handling report: {str(e)}")
        
        return redirect('admin_reports')
    
    # Get reports
    pending_reports = Report.objects.filter(is_resolved=False).order_by('priority_level', '-date')
    resolved_reports = Report.objects.filter(is_resolved=True).order_by('-resolved_date')[:20]
    
    # Stats
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


@require_http_methods(["GET"])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def api_stations(request):
    """API endpoint to get all stations with coordinates"""
    try:
        stations = Station.objects.filter(lat__isnull=False, lng__isnull=False)
        
        data = [{
            'station_id': station.station_id,
            'station_name': station.station_name,
            'lat': float(station.lat),
            'lng': float(station.lng)
        } for station in stations]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        import logging
        logging.error(f"Error in api_stations: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)


@require_http_methods(["GET"])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def api_routes(request):
    """API endpoint to get all route segments"""
    try:
        routes = Route.objects.select_related('from_station', 'to_station').filter(
            from_station__lat__isnull=False,
            from_station__lng__isnull=False,
            to_station__lat__isnull=False,
            to_station__lng__isnull=False
        )
        
        data = [{
            'route_id': route.route_id,
            'from_station_id': route.from_station.station_id,
            'to_station_id': route.to_station.station_id,
            'from_lat': float(route.from_station.lat),
            'from_lng': float(route.from_station.lng),
            'to_lat': float(route.to_station.lat),
            'to_lng': float(route.to_station.lng)
        } for route in routes]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        import logging
        logging.error(f"Error in api_routes: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)


def map_view(request):
    """Render the map page"""
    return render(request, 'map.html')