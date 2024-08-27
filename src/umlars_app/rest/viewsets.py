from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication

from umlars_app.models import UmlModel, UmlFile
from umlars_app.rest.permissions import IsOwner, IsFileOwner
from umlars_app.rest.serializers import UmlModelSerializer, UmlFileSerializer, UmlModelFilesSerializer


class UmlModelViewSet(viewsets.ModelViewSet):
    queryset = UmlModel.objects.all()
    serializer_class = UmlModelSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated & (IsAdminUser|IsOwner)]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return UmlModel.objects.all()
        return UmlModel.objects.filter(accessed_by__id=self.request.user.id)
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance.accessed_by.add(self.request.user)


class UmlFileViewSet(viewsets.ModelViewSet):
    queryset = UmlFile.objects.all()
    serializer_class = UmlFileSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated & (IsAdminUser|IsFileOwner)]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return UmlFile.objects.all()
        return UmlFile.objects.filter(model__accessed_by__id=self.request.user.id)
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance.model.accessed_by.add(self.request.user)


class UmlModelFilesViewSet(viewsets.ModelViewSet):
    queryset = UmlModel.objects.all().prefetch_related('source_files')
    serializer_class = UmlModelFilesSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated & (IsAdminUser|IsOwner)]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return UmlModel.objects.all().prefetch_related('source_files')
        return UmlModel.objects.filter(accessed_by__id=self.request.user.id).prefetch_related('source_files')
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance.accessed_by.add(self.request.user)
