from rest_framework import routers

from umli_app.viewsets import UmlModelViewSet, UmlModelMetadataViewSet

router = routers.SimpleRouter()

router.register(r'model', UmlModelViewSet, basename="model")
router.register(r'model-data', UmlModelMetadataViewSet, basename="model-data")

urlpatterns = router.urls