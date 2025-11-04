from rest_framework import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from courses.models import Enrollment, WatchedLesson
from courses.serializers import CourseSerializer

from django.db.models import Sum


class DashboardStatsView(APIView):
    def get(self, request: Request):

        user = request.user

        enrollments = Enrollment.objects.filter(
            user=user).select_related('course')

        courses = [enrollment.course for enrollment in enrollments]

        courses_data = CourseSerializer(courses, many=True).data

        total_courses = len(courses)
        total_reviews = user.reviews.count()
        total_watch_time = WatchedLesson.objects.filter(user=user).aggregate(
            total=Sum('lesson_time_estimate'))['total'] or 0

        total_certificates = 0

        for enrollment in enrollments:
            total_lessons = enrollment.course.modules.aggregate(
                total=Sum('lessouns__id'))['total'] or 0
            watched_lessons = user.watched_lessons.filter(
                lessons__module__course=enrollment.course).count()

            if total_lessons and watched_lessons >= total_lessons:
                total_certificates += 1

            return Response({
                'total_courses': total_courses,
                'total_reviews': total_reviews,
                'total_certificates': total_certificates,
                'total_watch_time': total_watch_time,
                'courses': courses_data
            })
