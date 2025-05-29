from django import forms
from .models import Student
from .models import Instructor
from django.db import connection


class GPAPredictionForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), label="Select Student")
    semester_id = forms.IntegerField(label="Predict for Semester", min_value=1, max_value=3)

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Upload GPA CSV")


class CourseRecommendationForm(forms.Form):
    instructor_name = forms.ChoiceField(
        label='Instructor Name',
        required=True,
        help_text="Select an instructor"
    )
    latest_semester_id = forms.IntegerField(
        label='Latest Semester ID',
        min_value=1,
        max_value=3,
        help_text="Enter semester ID between 1 and 3"
    )

    def __init__(self, *args, **kwargs):
        super(CourseRecommendationForm, self).__init__(*args, **kwargs)

        try:
            # Use ORM to fetch instructor names
            instructors = Instructor.objects.values_list('instructor_name', flat=True).distinct().order_by('instructor_name')

            if instructors.exists():
                # Convert to list of 2-tuples (value, label)
                self.fields['instructor_name'].choices = [
                    (name, name) for name in instructors
                ]
            else:
                self.fields['instructor_name'].choices = []
                self.fields['instructor_name'].help_text = "⚠️ No instructors found in the database."
        except Exception as e:
            self.fields['instructor_name'].choices = []
            self.fields['instructor_name'].help_text = f"❌ Error loading instructors: {str(e)}"