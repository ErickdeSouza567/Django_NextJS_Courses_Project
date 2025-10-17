from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from courses.filters import CourseFilter
from courses.models import Course
from courses.serializers import CourseSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    filterset_class = CourseFilter
    ordering_fields = ['price', 'created_at']
