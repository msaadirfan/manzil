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
    path('map',views.map,name='map'),
    ]