from django.contrib import admin
from .models import Contact, Contribute, Station, Route, Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'report_type', 'priority_level', 'name', 'email', 'date', 'is_resolved']
    list_filter = ['report_type', 'priority_level', 'is_resolved', 'date']
    search_fields = ['name', 'email', 'description']
    ordering = ['priority_level', '-date']
    readonly_fields = ['date', 'priority_level']
    
    fieldsets = (
        ('Reporter Information', {
            'fields': ('name', 'email')
        }),
        ('Report Details', {
            'fields': ('report_type', 'priority_level', 'description', 'date')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_date', 'admin_notes')
        }),
    )

admin.site.register(Contact)
admin.site.register(Contribute)
admin.site.register(Station)
admin.site.register(Route)