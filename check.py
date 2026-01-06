"""
Quick script to check if your database has coordinates
Run this to diagnose the issue
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manzilproject.settings')
django.setup()

from routefinder.models import Station, Route

print("=" * 60)
print("DATABASE DIAGNOSIS")
print("=" * 60)

# Check if Station model has latitude/longitude fields
print("\n1. Checking Station model fields...")
try:
    station = Station.objects.first()
    if station:
        print(f"   Sample station: {station.station_name}")
        print(f"   Has latitude field: {hasattr(station, 'latitude')}")
        print(f"   Has longitude field: {hasattr(station, 'longitude')}")
        
        if hasattr(station, 'latitude'):
            print(f"   Latitude value: {station.latitude}")
            print(f"   Longitude value: {station.longitude}")
    else:
        print("   ⚠️ No stations found in database!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check total stations
print("\n2. Checking station count...")
total_stations = Station.objects.count()
print(f"   Total stations in database: {total_stations}")

# Check stations with coordinates
print("\n3. Checking stations with coordinates...")
try:
    with_coords = Station.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False
    ).count()
    print(f"   Stations with coordinates: {with_coords}")
    
    if with_coords == 0:
        print("   ❌ NO COORDINATES FOUND!")
        print("   You need to:")
        print("   1. Run: python manage.py makemigrations")
        print("   2. Run: python manage.py migrate")
        print("   3. Import coordinates using the script")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("   Latitude/Longitude fields don't exist yet!")
    print("   Run migrations first!")

# Check routes
print("\n4. Checking routes...")
total_routes = Route.objects.count()
print(f"   Total route segments: {total_routes}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)