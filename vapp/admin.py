from django.contrib import admin

# Register your models here.

from .models import Professor, Module, Rating

admin.site.register(Professor)
admin.site.register(Rating)
admin.site.register(Module)
