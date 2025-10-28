from rest_framework import viewsets, decorators, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException, NotFound

from core.utils.exceptions import ValidationError
from core.utils.formatters import format_serializer_error
from courses.filters import CourseFilter
from courses.models import Course, Enrollment, Lesson, WatchedLesson
from courses.serializers import CourseSerializer, ReviewSerializer

from datetime import datetime

from django.db.models import Avg, Count, Sum


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    filterset_class = CourseFilter
    ordering_fields = ['price', 'created_at']

    @decorators.action(detail=True, methods=['get'])
    def reviews(self, request: Request, pk=None):
        course = self.get_object()
        reviews = course.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_review(self, request: Request, pk=None):
        course = self.get_object()
        user = request.user

        if not Enrollment.objects.filter(user=user, course=course).exists():
            raise APIException(
                "Você deve estar matriculado neste curso para enviar uma avaliação.")

        if course.reviews.filter(user=user).exists():
            raise APIException(
                "Você já enviou uma avaliação para este curso.")

        data = {"rating": request.data.get("rating"),
                "comment": request.data.get("comment")
                }

        serializer = ReviewSerializer(data=data)
        if not serializar.is_valid():
            raise ValidationError(format_serializer_error(serializer.errors))

        serializer.save(user=user, course=course)

        aggregate = course.reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id')
        )

        course.average_rating = aggregate['average_rating'] or 0
        course.total_reviews = aggregate['total_reviews'] or 0
        course.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        enrolled_at = None
        if request.user.is_autheticated:
            enrolled = Enrollment.objects.filter(
                user=request.user,
                course=instance
            ).first()
            if enrolled:
                enrolled_at = enrolled.enrolled_at

        return Response({
            **serializer.data,
            'enrolled_at': enrolled_at
        })

    @decorators.action(detail=True, methods=['get'])
    def content(self, request: Request, pk=None):
        course = self.get_object()

        modules = Module.objects.filter(course=course)
        total_modules = modules.count()

        lessons = Lesson.objects.filter(module__course=course)
        total_lessons = lessons.count()

        total_time = lessons.aggregate(
            total=Sum('time_estimate')
        )['total'] or 0

        watched_lessons.count = 0
        watched_lessons_set = set()

        if request.user.is_authenticated:
            watched_lessons = WatchedLesson.objects.filter(
                user=request.user,
                lessons__in=lessons
            ).values_list('lesson_id', flat=True)

            watched_lessons_set = set(watched_lessons)
            watched_lessons_count = len(watched_lessons_set)

        progress = 0
        if total_lessons > 0:
            progress = round((watched_lessons_count / total_lessons) * 100, 2)

        modules_data = ModuleSerializer(modules, many=True).data

        for module in modules_data:
            for lesson in module['lessons']:
                lesson['is_watched'] = lesson['id'] in watched_lessons_set

        return Response({
            'total_modules': total_modules,
            'total_lessons': total_lessons,
            'total_time_estimate': total_time,
            'progress': progress,
            'modules': modules_data})

    @decorators.action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def certificate(self, request: Request, pk=None):
        course = self.get_object()
        user = request.user

        if not Enrollment.objects.filter(user=user, course=course).exists():
            raise APIException(
                "Você deve estar matriculado neste curso para enviar uma avaliação.")

        lessons = Lesson.objects.filter(
            module__course=course).values_list('id', flat=True)
        total_lessons = lessons.count()
        watched_lessons = WatchedLesson.objects.filter(
            user=user,
            lesson_id__in=lessons
        ).count()

        if total_lessons == 0 or (watched_lessons / total_lessons) < 1:
            raise APIException(
                "Você deve completar todas as aulas deste curso para obter o certificado.")

        progress = (watched_lessons / total_lessons) * \
            100 if total_lessons > 0 else 0

        course_data = CourseSerializer(course).data
        certificate_data = {
            'issued_at': datetime.now(),
            'progress': progress

        }

        return Response({
            "course": course_data,
            "certificate": certificate_data

        })


class LessonMarkAsWatchedView(views.APIView):
    def post(self, request: Request, lesson_id: None):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            raise NotFound('Aula não encontrada.')

        watched, created = WatchedLesson.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )

        if created:
            return Response({'detail': 'Aula marcada como assistida.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Aula já estava marcada como assistida.'})
