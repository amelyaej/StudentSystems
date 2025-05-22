from django.contrib import admin
from .models import Department, Student, GPARecord, MLModel
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
import joblib
import os
from django.conf import settings
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from django.contrib import messages
from django.http import HttpResponseRedirect


# === DEPARTMENT ADMIN ===
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_id', 'dept_name')
    search_fields = ('dept_name',)
    ordering = ('dept_id',)


# === CUSTOM ACTION: Retrain Model ===
def train_and_save_model(modeladmin, request, queryset):
    try:
        records = GPARecord.objects.all().values()
        if not records.exists():
            messages.error(request, "❌ No training data available. Please add GPA records first.")
            return

        df = pd.DataFrame.from_records(records)
        
        # Ensure there's data to train on
        if df.empty:
            messages.warning(request, "⚠️ No GPA records found to train the model.")
            return

        # Handle missing values if any
        df = df.dropna()
        
        # Check if we still have data after dropping NA
        if df.empty:
            messages.error(request, "❌ No valid data available after cleaning.")
            return

        X = df[['avg_grade', 'attendance_percentage', 'assessment_count', 'avg_score']]
        y = df['gpa_drop']

        model = RandomForestClassifier(random_state=42)
        model.fit(X, y)

        predictions = model.predict(X)

        report = classification_report(y, predictions, output_dict=True)
        accuracy = round(accuracy_score(y, predictions) * 100, 2)
        precision = round(report['weighted avg']['precision'] * 100, 2)
        recall = round(report['weighted avg']['recall'] * 100, 2)
        f1_score_val = round(report['weighted avg']['f1-score'] * 100, 2)

        # Define model save path
        models_dir = os.path.join(settings.BASE_DIR, 'final_app', 'models')
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, 'gpa_drop_model.pkl')
        joblib.dump(model, model_path)

        # Update or create MLModel entry
        ml_model, created = MLModel.objects.update_or_create(
            name="Random Forest GPA Predictor",
            defaults={
                'description': "Automatically trained on student GPA drop dataset",
                'model_type': "classification",
                'use_case': "GPA Drop Prediction",
                'dataset': "Student Performance Dataset",
                'file_path': model_path,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score_val,
            }
        )

        msg = "✅ Model created and trained successfully!" if created else "✅ Model retrained and updated successfully!"
        messages.success(request, msg)

    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


# === STUDENT ADMIN ===
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('stu_id', 'name', 'email', 'dept', 'view_details_link')
    search_fields = ('name', 'email', 'stu_id')
    list_filter = ('dept',)
    ordering = ('stu_id',)
    readonly_fields = ('stu_id',)
    list_per_page = 20
    change_list_template = 'admin/student_change_list.html'

    def view_details_link(self, obj):
        url = reverse('admin:final_app_student_details', args=[obj.pk])
        return format_html('<a class="button" href="{}">View Details</a>', url)

    view_details_link.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:student_id>/details/', 
                 self.admin_site.admin_view(self.student_details_view),
                 name='final_app_student_details'),
        ]
        return custom_urls + urls

    def student_details_view(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
            gpa_records = GPARecord.objects.filter(student=student).order_by('semester')

            context = dict(
                self.admin_site.each_context(request),
                title=f"Student Details: {student.name}",
                student=student,
                gpa_records=gpa_records,
                opts=self.model._meta,
            )
            return render(request, 'admin/student_details.html', context)
        except Student.DoesNotExist:
            messages.error(request, "Student not found")
            return redirect('admin:final_app_student_changelist')


# === GPA RECORD ADMIN ===
@admin.register(GPARecord)
class GPARecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'avg_grade', 'attendance_percentage', 
                   'gpa_drop', 'delete_button')
    list_filter = ('gpa_drop', 'semester')
    search_fields = ('student__name', 'student__stu_id', 'semester')
    ordering = ('student', 'semester')
    list_per_page = 20
    list_select_related = ('student',)

    fieldsets = (
        ('Student Info', {
            'fields': ('student', 'semester')
        }),
        ('Performance Data', {
            'fields': ('avg_grade', 'attendance_percentage', 'assessment_count', 'avg_score', 'prev_gpa')
        }),
        ('Prediction Result', {
            'fields': ('gpa_drop',)
        }),
    )

    def delete_button(self, obj):
        url = reverse('admin:final_app_gparecord_delete', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" onclick="return confirm(\'Are you sure?\')">Delete</a>',
            url
        )

    delete_button.short_description = 'Actions'


# === ML MODEL ADMIN ===
@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    CREATOR_CHOICES = [
        ('Ijlal', 'Ijlal'),
        ('Dadia', 'Dadia'),
        ('Shynny', 'Shynny'),
        ('Amel', 'Amel'),
    ]

    list_display = ('name', 'model_type', 'use_case', 'created_at', 
                   'creator', 'accuracy', 'precision', 'retrain_link')
    list_filter = ('model_type', 'use_case', 'creator')
    search_fields = ('name', 'description', 'creator')
    readonly_fields = ('created_at', 'file_path', 'accuracy', 
                      'precision', 'recall', 'f1_score')
    change_list_template = 'admin/mlmodel_change_list.html'
    actions = [train_and_save_model]

    fieldsets = (
        ('Model Information', {
            'fields': ('name', 'description', 'model_type', 'use_case', 'dataset', 'creator')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score')
        }),
        ('Technical Details', {
            'fields': ('file_path', 'created_at')
        }),
    )

    def retrain_link(self, obj):
        url = reverse('admin:final_app_mlmodel_retrain', args=[obj.pk])
        return format_html('<a class="button" href="{}">Retrain</a>', url)

    retrain_link.short_description = 'Retrain'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/retrain/', 
                 self.admin_site.admin_view(self.retrain_model),
                 name='final_app_mlmodel_retrain'),
        ]
        return custom_urls + urls

    def retrain_model(self, request, pk):
        try:
            queryset = MLModel.objects.filter(pk=pk)
            train_and_save_model(self, request, queryset)
        except Exception as e:
            messages.error(request, f"❌ Error retraining model: {str(e)}")
        return HttpResponseRedirect(reverse('admin:final_app_mlmodel_changelist'))