from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/', views.predict_gpa, name='predict_gpa'),
    path('predict-attendance/', views.attendance_predict_view, name='attendance_predict'),
]
