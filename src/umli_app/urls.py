from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from umli_app.routers import router
from umli_app import views

urlpatterns = [
    path("", views.home, name="home"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("uml-model/<int:pk>", views.uml_model, name="uml-model"),
    path("delete-uml-model/<int:pk>", views.delete_uml_model, name="delete-uml-model"),
    path("update-uml-model/<int:pk>", views.update_uml_model, name="update-uml-model"),
    path("add-uml-model/", views.add_uml_model, name="add-uml-model"),
    path("bulk-upload-uml-models/", views.bulk_upload_uml_models, name="bulk-upload-uml-models"),
    path("review-bulk-upload-uml-models/", views.review_bulk_upload_uml_models, name="review-bulk-upload-uml-models"),

    path('api/', include((router.urls, 'core_api'), namespace='core_api')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
# static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
