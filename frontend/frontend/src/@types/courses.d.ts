type CourseLevel = "beginner" | "intermediate" | "advanced"


type CourseTag = {
    id: number;
    name: string;
}

type Course = {
    id: number;
    tags: CourseTag[];
    title: string;
    description: string;
    thumbnail: string;
    price: number;
    level: CourseLevel;
    total_enrollments: number;
    author: {
        name: string;
        email: string;
        average_rating: number;
        total_courses: number;
    };
    total_reviews: number;
    average_rating: number;
    enrolled_at: string | null;
    created_at: string;
}

type CourserLesson = {
    id: number;
    title: string;
    description: string;
    video_url: string;
    time_estimate: number;
    is_watched: boolean;
    created_at: string;
}

type CourseModule = {
    id: number;
    title: string;
    lessons: CourseLesson[]
}

type CourseReview = {
    id: number;
    user: string;
    rating: number;
    comment: string;
    created_at: string;
}

type APIGetCourseResponse = Course;

type APIGetCoursesResponse = {
    results: Course[];
    count: number;
    next: string | null;
    previous: string | null;
}

type APIGetCourseContentResponse = {
    total_modules: number;
    total_time: number;
    total_lessons: number;
    progress: number;
    modules: CourseModule[]
}

type APIGetCourseReviewsResponse = CourseReview[]

type APIGetCourseCertificateResponse = {
    course: Course;
    certificate: {
        progress: number;
        issued_at: string;
    }
}


type APIPostCourseEnrollResponse = {
    checkout_url: string;
}