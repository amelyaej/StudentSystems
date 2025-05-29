from django.urls import path
from . import views
from .views import engagement_ratio

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/', views.predict_gpa, name='predict_gpa'),
    path('predict-attendance/', views.attendance_predict_view, name='attendance_predict'),
    path('engagement-ratio/', engagement_ratio, name='engagement_ratio'),
]
