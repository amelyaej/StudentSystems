from django.shortcuts import render
from .forms import GPAPredictionForm
from .models import GPARecord
import pandas as pd
import joblib
import os
from django.conf import settings

# Global variable to cache the model
_model = None
_model_metrics = None

def get_model():
    """
    Load the trained model only once.
    """
    global _model
    if _model is None:
        MODEL_PATH = os.path.join(settings.BASE_DIR, 'final_app', 'models', 'gpa_drop_model.pkl')
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception as e:
            raise RuntimeError(f"Error loading model: {e}")
    return _model

def get_model_metrics():
    """
    Load the trained model only once.
    """
    global _model_metrics
    if _model_metrics is None:
        METRICS_PATH = os.path.join(settings.BASE_DIR, 'final_app', 'models', 'gpa_drop_model_metrics.pkl')
        try:
            _model_metrics = joblib.load(METRICS_PATH)
            if not all(key in _model_metrics for key in ['model_name', 'accuracy', 'precision', 'recall', 'f1_score']):
                raise ValueError("Metrics file missing required fields")
        except Exception as e:
            print(f"Warning: Could not load metrics - {e}")
            _model_metrics = {
                'model_name': 'GPA Drop Metrics',
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0
            }
    return _model_metrics

def home(request):
    """
    Render the homepage.
    """
    return render(request, 'home.html')

def predict_gpa(request):
    """
    Handle GPA drop prediction requests.
    - Validates form input
    - Fetches relevant GPA records
    - Predicts GPA drop using latest semester data
    - Returns results to template for display
    """
    model = get_model()
    metrics = get_model_metrics()
    predicted_records = None
    predicted_results = None
    changes = None  # Initialize changes dictionary

    if request.method == 'POST':
        form = GPAPredictionForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            semester_id = form.cleaned_data['semester_id']

            # Ensure semester_id is an integer
            try:
                semester_id = int(semester_id)
            except (ValueError, TypeError):
                semester_id = 1

            # Get all GPA records up to the selected semester
            previous_records = GPARecord.objects.filter(
                student=student,
                semester_id__lte=semester_id
            ).order_by('semester_id')

            latest_record = previous_records.last()

            if latest_record is None:
                # No previous records found
                predicted_results = {
                    'student': student,
                    'semester_id': semester_id,
                    'prediction': "No previous GPA records found for this student."
                }
                predicted_records = {
                    'student': student,
                    'semester_id': semester_id,
                    'prev_records': [],
                    'labels': [],
                    'avg_grades': [],
                    'attendance_percentages': [],
                    'avg_scores': []
                }

            elif semester_id == 1 or previous_records.count() == 1:
                # First semester, no prior GPA to compare
                predicted_results = {
                    'student': student,
                    'semester_id': semester_id,
                    'prediction': "This is the student's first semester — no prior GPA to compare or track."
                }
                predicted_records = {
                    'student': student,
                    'semester_id': semester_id,
                    'current_record': latest_record,
                    'prev_records': previous_records,
                    'labels': [r.semester_id for r in previous_records],
                    'avg_grades': [float(r.avg_grade) for r in previous_records],
                }

            else:
                # For semesters > 1, predict GPA drop using latest record features
                features = pd.DataFrame([{
                    'semester_id': latest_record.semester_id,
                    'avg_grade': latest_record.avg_grade,
                    'attendance_percentage': latest_record.attendance_percentage,
                    'avg_score': latest_record.avg_score,
                    'assessment_count': latest_record.assessment_count
                }])

                try:
                    prediction = model.predict(features)[0]
                    confidence = round(model.predict_proba(features)[0][1] * 100, 2)
                except Exception as e:
                    prediction = f"Error during prediction: {e}"
                    confidence = None

                # Calculate changes from previous semester
                if previous_records.count() > 1:
                    previous_record = previous_records[previous_records.count()-2]  # Second last record
                    try:
                        grade_change = round(latest_record.avg_grade - previous_record.avg_grade, 2)
                        grade_change_pct = round((grade_change / previous_record.avg_grade) * 100, 1)
                        attendance_change = round(latest_record.attendance_percentage - previous_record.attendance_percentage, 2)
                        attendance_change_pct = round((attendance_change / previous_record.attendance_percentage) * 100, 1)

                        changes = {
                            'grade_change': grade_change,
                            'grade_change_pct': grade_change_pct,
                            'attendance_change': attendance_change,
                            'attendance_change_pct': attendance_change_pct,
                        }
                    except (AttributeError, TypeError, ZeroDivisionError) as e:
                        print(f"Error calculating changes: {e}")

                predicted_results = {
                    'student': student,
                    'semester_id': semester_id,
                    'prediction': "Yes" if prediction == 1 else "No",
                    'confidence': confidence,
                    'changes': changes
                }

                predicted_records = {
                    'student': student,
                    'semester_id': semester_id,
                    'current_record': latest_record,
                    'prev_records': previous_records,
                    'labels': [r.semester_id for r in previous_records],
                    'avg_grades': [float(r.avg_grade) for r in previous_records],
                    'attendance_percentages': [float(r.attendance_percentage) for r in previous_records],
                    'avg_scores': [float(r.avg_score) for r in previous_records] if hasattr(previous_records[0], 'avg_score') else []
                }

        else:
            predicted_results = None
            predicted_records = None

    else:
        form = GPAPredictionForm()

    return render(request, 'predict.html', {
        'form': form,
        'predicted_records': predicted_records,
        'prediction': predicted_results,
        'metrics': metrics,
    })
