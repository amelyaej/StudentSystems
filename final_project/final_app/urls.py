from django.urls import path
<<<<<<< HEAD
from . import views
from .views import engagement_ratio

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/', views.predict_gpa, name='predict_gpa'),
    path('predict-attendance/', views.attendance_predict_view, name='attendance_predict'),
    path('engagement-ratio/', engagement_ratio, name='engagement_ratio'),
=======
from .views import retrain_model_view, predict_gpa, home, attendance_predict_view
from django.contrib import admin

urlpatterns = [
    path('', home, name='home'),
    path('predict-attendance/', attendance_predict_view, name='attendance_predict'),
    path('admin/', admin.site.urls),
    path('retrain-model/<int:model_id>/', retrain_model_view, name='retrain-model'),
    # path('', home, name='home'),
    path('predict_gpa/', predict_gpa, name='predict_gpa'),
>>>>>>> 30d2e8b0ad91e6102afde4410c2ea417d483c4f5
]

# from django.urls import path, include
# from . import views
# from django.contrib import admin
# from .views import retrain_model_view, predict_gpa, home

# urlpatterns = [
#     path('admin/', include([
#         path('', admin.site.urls),
#         path('admin/retrain-model/', retrain_model_view, name='retrain-model'),
#     ])),
#     path('', home, name='home'),
#     path('predict_gpa/', predict_gpa, name='predict_gpa'),
# ]

