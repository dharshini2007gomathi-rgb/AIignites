"""REST API views for applications."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStudent, IsIndustryOrFaculty, IsAdminRole
from accounts.utils import send_application_status_email
from applications.models import Application
from applications.serializers import ApplicationSerializer, ApplicationStatusSerializer


class ApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = user.profile
        if profile.is_student:
            return Application.objects.filter(student=user.student)
        elif profile.is_industry:
            return Application.objects.filter(opportunity__industry=user.industry)
        elif profile.is_faculty:
            return Application.objects.filter(opportunity__faculty=user.faculty)
        return Application.objects.all()

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student)


class ApplicationDetailView(generics.RetrieveAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'application_id'


class ApplicationStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsIndustryOrFaculty]

    def put(self, request, application_id):
        application = Application.objects.get(application_id=application_id)
        serializer = ApplicationStatusSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            send_application_status_email(application)
            return Response(ApplicationSerializer(application).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
