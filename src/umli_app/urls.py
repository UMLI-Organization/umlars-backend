from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('uml-model/<int:pk>', views.uml_model, name='uml-model'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
