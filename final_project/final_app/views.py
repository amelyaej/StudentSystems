from django.shortcuts import render
from .forms import GPAPredictionForm
from .models import GPARecord

def home(request):
    return render(request, 'home.html')

def predict_gpa(request):
    predicted_records = None
    labels = []
    data = []

    if request.method == 'POST':
        form = GPAPredictionForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            semester_id = form.cleaned_data['semester_id']

            previous_records = GPARecord.objects.filter(student=student, semester_id__lte=semester_id).order_by('semester_id')
            for r in previous_records:
                labels.append(f"Semester {r.semester_id}")
                data.append(r.avg_grade)

            predicted_records = {
                'student': student,
                'semester_id': semester_id,
                'prev_records': previous_records,
                'labels': labels,
                'data': data
            }
    else:
        form = GPAPredictionForm()

    return render(request, 'predict.html', {'form': form, 'predicted_records': predicted_records})