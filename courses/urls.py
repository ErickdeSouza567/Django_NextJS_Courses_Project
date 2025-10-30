from rest_framework import DefaultRouter
from django.urls import path

from courses.views import CourseViewSet, LessonMarkAsWatchedView, ProccessCheckoutView

router = DefaultRouter()
router.register('', CourseViewSet, basename='course')

urlpatterns = router.urls + [
    path('proccess-checkout/', ProccessCheckoutView.as_view()),
    path('lessons/<int:lesson_id>/watched/', LessonMarkAsWatchedView.as_view())
]
