from django_filters import rest_framework as filters
from courses.models import Course


class CourseFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="price", lookup_expr='lte')
    title = filters.CharFilter(field_name="title", lookup_expr='icontains')
    level = filters.CharFilter(field_name="level", lookup_expr='iexact')
    tags = filters.BaseInFilter(field_name="tags__name", lookup_expr='in')

    class Meta:
        model = Course
        fields = ['price_min', 'price_max', 'title', 'level', 'tags']
