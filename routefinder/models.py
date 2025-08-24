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
    station_id=models.IntegerField()
    station_name=models.CharField(max_length=200)

    def __str__(self):
        return self.station_name

class Route(models.Model):
    route_id = models.CharField(max_length=10)
    from_station = models.ForeignKey(Station, related_name="routes_from", on_delete=models.CASCADE)
    to_station = models.ForeignKey(Station, related_name="routes_to", on_delete=models.CASCADE)
    distance_kms = models.FloatField()
