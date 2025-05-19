from django.contrib import admin
from .models import Student, GPARecord

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('stu_id', 'name')
    search_fields = ('name',)
    ordering = ('stu_id',)

@admin.register(GPARecord)
class GPARecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester_id', 'avg_grade', 'attendance_percentage', 'assessment_count', 'gpa_drop')
    list_filter = ('gpa_drop', 'semester_id')
    search_fields = ('student__name',)
    ordering = ('student', 'semester_id')