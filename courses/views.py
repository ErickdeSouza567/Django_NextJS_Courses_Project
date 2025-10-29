from rest_framework import viewsets, decorators, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException, NotFound
from rest_framework import status

from core.utils.exceptions import ValidationError
from core.utils.formatters import format_serializer_error
from courses.filters import CourseFilter
from courses.models import Course, Enrollment, Lesson, Order, WatchedLesson
from courses.serializers import CourseSerializer, ReviewSerializer
from courses.models import Module
from courses.serializers import ModuleSerializer

from datetime import datetime

from django.db.models import Avg, Count, Sum
from django.conf import settings

import stripe


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    filterset_class = CourseFilter
    ordering_fields = ['price', 'created_at']

    def _get_course_and_validate_enrollment(self, request: Request, require_enrollment=True):
        course = self.get_object()
        user = request.user

        is_enrolled = Enrollment.objects.filter(
            user=user, course=course).exists()

        if require_enrollment and not is_enrolled:
            raise APIException(
                "Você deve estar matriculado neste curso.")

        if not require_enrollment and is_enrolled:
            raise APIException(
                "Você já está matriculado neste curso."
            )

        return course, user

    def _get_watched_progress(self, user, course, with_total_time=False):
        lessons = Lesson.objects.filter(
            module__course=course).values_list('id', flat=True)
        total_lessons = len(lessons)

        total_time = 0
        if with_total_time:
            total_time = lessons.aggregate(
                total=Sum('time_estimate')
            )['total'] or 0

        watched_lessons = []
        total_watched_lessons = 0
        if user is not None:
            watched_lessons = WatchedLesson.objects.filter(
                user=user,
                lesson_id__in=lessons
            ).values_list('lesson_id', flat=True)
            total_watched_lessons = len(watched_lessons)

        return {
            "lessons": lessons,
            "total_lessons": total_lessons,
            "watched_lessons": watched_lessons,
            "total_time": total_time,
            "progress": round((total_watched_lessons / total_lessons) * 100, 2) if total_watched_lessons > 0 and total_lessons > 0 else 0
        }

    @decorators.action(detail=True, methods=['get'])
    def reviews(self, request: Request, pk=None):
        course = self.get_object()
        reviews = course.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_review(self, request: Request, pk=None):

        course, user = self._get_course_and_validate_enrollment(request)

        if course.reviews.filter(user=user).exists():
            raise APIException(
                "Você já enviou uma avaliação para este curso.")

        data = {"rating": request.data.get("rating"),
                "comment": request.data.get("comment")
                }

        serializer = ReviewSerializer(data=data)
        if not serializer.is_valid():
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
        if request.user.is_authenticated:
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
        user = request.user

        modules = Module.objects.filter(course=course)
        total_modules = modules.count()

        watched_progress = self._get_watched_progress(
            user if request.user.is_authenticated else None,
            course,
            with_total_time=True
        )

        modules_data = ModuleSerializer(modules, many=True).data

        for module in modules_data:
            for lesson in module['lessons']:
                lesson['is_watched'] = lesson['id'] in watched_progress.get(
                    'watched_lessons', [])

        return Response({
            'total_modules': watched_progress.get('total_modules', total_modules),
            'total_lessons': watched_progress.get('total_lessons', 0),
            'total_time_estimate': watched_progress.get('total_time', 0),
            'progress': watched_progress.get('progress', 0),
            'modules': modules_data})

    @decorators.action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def certificate(self, request: Request, pk=None):

        course, user = self._get_course_and_validate_enrollment(request)

        watched_progress = self._get_watched_progress(
            user,
            course,
            with_total_time=True
        )

        if watched_progress.get('progress') < 100:
            raise APIException(
                "Você deve completar todas as aulas deste curso para obter o certificado.")

        course_data = CourseSerializer(course).data
        certificate_data = {
            'issued_at': datetime.now(),
            'progress': watched_progress.get('progress')

        }

        return Response({
            "course": course_data,
            "certificate": certificate_data

        })

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request: Request, pk=None):
        course, user = self._get_course_and_validate_enrollment(
            request, require_enrollment=False)

        if Order.objects.filter(user=user, course=course, paid=True).exists():
            raise APIException(
                "Você já possui um pedido pago para este curso.")

        user.orders.filter(course=course, paid=False).delete()

        order = Order.objects.create(
            user=user,
            course=course,
        )
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': course.title,
                            'description': course.description,
                        },
                        'unit_amount': int(course.price * 100),
                    },
                    'quantity': 1,
                }],
                customer_email=user.email,
                metadata={
                    'user_id': user.id,
                    'course_id': course.id,
                    'order_id': order.id,
                },
                success_url=f'{settings.BASE_URL}/api/v1/courses/process_checkout?order_id={order.id}',
                cancel_url=f'{settings.FRONTEND_BASE_URL}/courses/{course.id}?message=cancel_order',
            )

            order.external_payment_id = checkout_session.id
            order.save()

        except Exception as e:
            return Response({'detail': 'Erro ao tentar se inscrever no curso.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )


class LessonMarkAsWatchedView(views.APIView):
    def post(self, request: Request, lesson_id: int):
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
