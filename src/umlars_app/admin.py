from django.contrib import admin

from .models import UmlModel, UmlModelMetadata, UmlFile

admin.site.register(UmlModel)
admin.site.register(UmlFile)
admin.site.register(UmlModelMetadata)
