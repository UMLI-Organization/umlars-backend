from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from umlars_app.rest.routers import urlpatterns as rest_viewsets_urlpatterns
from umlars_app.rest.urls import urlpatterns as rest_views_urlpatterns
from umlars_app import views

urlpatterns = [
    path("", views.home, name="home"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("profile/", views.profile, name="profile"),
    path("delete-current-user/", views.delete_current_user, name="delete-current-user"),
    path("profile/change-password/", views.change_password, name="profile/change-password"),
    path("uml-model/<int:pk>", views.uml_model, name="uml-model"),
    path("delete-uml-model/<int:pk>", views.delete_uml_model, name="delete-uml-model"),
    path("translate-uml-model/<int:pk>", views.translate_uml_model, name="translate-uml-model"),
    path("update-uml-model/<int:pk>", views.update_uml_model, name="update-uml-model"),
    path("add-uml-model/", views.add_uml_model, name="add-uml-model"),
    path("bulk-upload-uml-models/", views.bulk_upload_uml_models, name="bulk-upload-uml-models"),
    path("review-bulk-upload-uml-models/", views.review_bulk_upload_uml_models, name="review-bulk-upload-uml-models"),
    path('share-model/<int:model_id>', views.share_model, name='share-model'),
    path('select2/', include('django_select2.urls')),  # Include the django_select2 URLs


    # path('api/v1/', include('rest_framework.urls')),
    path('api/v1/', include((rest_viewsets_urlpatterns, 'rest_viewsets'), namespace='rest_viewsets')),
    path('api/v1/', include((rest_views_urlpatterns, 'rest_views'), namespace='rest_views')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
# static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
