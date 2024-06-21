from django.contrib import admin

from .models import UmlModel, UmlModelMetadata

admin.site.register(UmlModel)
admin.site.register(UmlModelMetadata)
