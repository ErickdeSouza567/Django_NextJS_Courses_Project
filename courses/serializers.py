from rest_framework import serializers

from accounts.models import User
from courses.models import Course, Tag, Review, Lesson, Module

from django.db.models import Avg


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CourseAuthorSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_courses = serializers.SerializerMethodField()

    class Meta:
        model = Userfelds = ['name',
                             'email',
                             'average_rating',
                             'total_courses']

    def get_average_rating(self, obj: User):
        return round(obj.courses.aggregate(average_rating=Avg('average_rating'))['average_rating'] or 0)

    def get_total_courses(self, obj):
        return obj.courses.count()


class CourseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CourseAuthorSerializer(read_only=True)
    total__enrollments = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_total_enrollments(self, obj):
        return obj.enrollments.count()


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title',
                  'description',
                  'video_url',
                  'time_estimate',
                  'created_at']


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id',
                  'title',
                  'created_at',
                  'lessons']
