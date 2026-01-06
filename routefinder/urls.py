from django.urls import path
from . import views

urlpatterns=[
    path('',views.home,name='home'),
    path('routes',views.routes,name='routes'),
    path('contribute',views.contribute,name='contribute'),
    path('contact',views.contact,name='contact'),
    path('home',views.home,name='home'),
    path('stations/',views.station_search,name='station_search'),
    path('find_route',views.find_route,name='find_route'),
    
    # Map view and APIs
    path('map',views.map_view,name='map'),
    path('api/stations/',views.api_stations,name='api_stations'),
    path('api/routes/',views.api_routes,name='api_routes'),
    
    # Admin routes
    path('manzil-admin/reports', views.admin_reports, name='admin_reports'),
    path('manzil-admin/login', views.admin_login, name='admin_login'),
    path('manzil-admin/logout', views.admin_logout, name='admin_logout'),
]