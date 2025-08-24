def get_route_name(route_id):
    
    name_map = {
        'R1': 'Red Line 1/Pink Bus',
        'R2': 'Red Line 2/Pink Bus',
        'R3': 'Red Line 3/Pink Bus',
        'R4': 'Red Line 4',
        'R8': 'Red Line 8',
        'R9': 'Red Line 9/Pink Bus',
        'R10': 'Red Line 10/Pink Bus',
        'R11': 'Red Line 11',
        'R12': 'Red Line 12',
        'R13': 'Red Line 13',
        'EV1': 'EV1',
        'EV2': 'EV2',
        'EV3': 'EV3',
        'EV4': 'EV4',
        'EV5': 'EV5',
        'GL': 'Green Line',
        'OL': 'Orange Line',
    }
    return name_map.get(route_id, f'Route {route_id}')

def get_route_color(route_id):
   
    color_map = {
        'R1': '#ff7e1d',   # Red
        'R2': '#b20447',   # Blue
        'R3': '#0dd625',   # Green
        'R4': '#270072',   # Orange
        'R8': '#f4382f',   # Purple
        'R9': '#055aa0',   # Turquoise
        'R10': '#f2da00',  # Orange
        'R11': '#7c4872',  # Dark Blue
        'R12': '#8e008b',  # Pink
        'R13': '#630902',  # Deep Orange
        'EV1': '#630902',  # Light Green
        'EV2': '#630902',  # Cyan
        'EV3': '#5e3503',  # Amber
        'EV4': '#ff0098',  # Brown
        'EV5': '#bc9800',  # Blue Grey
        'GL': '#114c02',   # Light Green
        'OL': '#d85a14',   # Yellow
    }

from django import template
register = template.Library()

@register.filter
def route_color(route_id):
    return get_route_color(route_id)

@register.filter
def route_name(route_id):
    return get_route_name(route_id)