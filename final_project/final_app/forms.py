from django import forms
from .models import Student

class GPAPredictionForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), label="Select Student")
    semester_id = forms.IntegerField(label="Predict for Semester", min_value=1, max_value=3)