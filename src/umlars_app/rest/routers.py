from rest_framework import routers

from umlars_app.rest.viewsets import UmlModelViewSet, UmlModelMetadataViewSet, UmlFileViewSet, UmlModelFilesViewSet

router = routers.SimpleRouter()

router.register(r'models', UmlModelViewSet, basename="models")
router.register(r'model-metadata', UmlModelMetadataViewSet, basename="model-metadata")
router.register(r'files', UmlFileViewSet, basename="files")
router.register(r'model-files', UmlModelFilesViewSet, basename="model-files")


urlpatterns = router.urls