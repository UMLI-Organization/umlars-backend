from django.contrib import admin

from .models import UmlModel, UmlFile, UserAccessToModel

admin.site.register(UmlModel)
admin.site.register(UmlFile)
admin.site.register(UserAccessToModel)

