from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from umlars_app.models import UmlModel, UmlModelMetadata, UmlFile
from umlars_app.rest.serializers import UmlModelSerializer, UmlModelMetadataSerializer, UmlFileSerializer, UmlModelFilesSerializer


class UmlModelViewSet(viewsets.ModelViewSet):
    queryset = UmlModel.objects.all()
    serializer_class = UmlModelSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]



class UmlModelMetadataViewSet(viewsets.ModelViewSet):
    queryset = UmlModelMetadata.objects.all()
    serializer_class = UmlModelMetadataSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]



class UmlFileViewSet(viewsets.ModelViewSet):
    queryset = UmlFile.objects.all()
    serializer_class = UmlFileSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]



class UmlModelFilesViewSet(viewsets.ModelViewSet):
    queryset = UmlModel.objects.all().prefetch_related('source_files')
    serializer_class = UmlModelFilesSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]



