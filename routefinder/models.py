from django.db import models

# Create your models here.
class Contact(models.Model):
    name=models.CharField(max_length=122)
    email=models.CharField(max_length=122)
    desc=models.TextField()
    date=models.DateField()

class Contribute(models.Model):
    name=models.CharField(max_length=122)
    email=models.CharField(max_length=122)
    desc=models.TextField()
    date=models.DateField()

class Station(models.Model):
    station_id = models.IntegerField()
    station_name = models.CharField(max_length=200)
    lat = models.FloatField(null=True, blank=True)      # ADD THIS - matching your DB
    lng = models.FloatField(null=True, blank=True)      # ADD THIS - matching your DB

    def __str__(self):
        return self.station_name

class Route(models.Model):
    route_id = models.CharField(max_length=10)
    from_station = models.ForeignKey(Station, related_name="routes_from", on_delete=models.CASCADE)
    to_station = models.ForeignKey(Station, related_name="routes_to", on_delete=models.CASCADE)
    distance_kms = models.FloatField()

class Report(models.Model):
    REPORT_TYPES = [
        ('harassment', 'Harassment'),
        ('safety_hazard', 'Safety Hazard'),
        ('staff_behaviour', 'Staff Behaviour'),
        ('cleanliness', 'Cleanliness'),
        ('other', 'Other'),
    ]
    
    PRIORITY_LEVELS = [
        (1, 'Critical - Harassment'),
        (2, 'High - Safety Hazard'),
        (3, 'Medium - Staff Behaviour'),
        (4, 'Low - Cleanliness'),
        (5, 'Low - Other'),
    ]
    
    name = models.CharField(max_length=122)
    email = models.EmailField(max_length=122)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    priority_level = models.IntegerField(choices=PRIORITY_LEVELS)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['priority_level', '-date']  # Order by priority, then most recent
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.name} ({self.date.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Automatically set priority based on report type
        priority_map = {
            'harassment': 1,
            'safety_hazard': 2,
            'staff_behaviour': 3,
            'cleanliness': 4,
            'other': 5,
        }
        self.priority_level = priority_map.get(self.report_type, 5)
        super().save(*args, **kwargs)