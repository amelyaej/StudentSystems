from django.shortcuts import render
from .forms import GPAPredictionForm, UploadFileForm
from .models import GPARecord
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd
import joblib
import os
from django.conf import settings
import csv
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import CourseRecommendationForm
from django.db import connection
import pickle

# Global model and metrics cache
_model = None
_model_metrics = None

def attendance_predict_view(request):
    prediction = None

    if request.method == 'POST':
        try:
            attendance = float(request.POST.get('attendance'))
            if 0 <= attendance <= 100:
                model = joblib.load('final_app/models/attendance_gpa_model.pkl')
                grade = model.predict(np.array([[attendance]]))[0]
                gpa = round((grade / 100) * 4.0, 2)
                prediction = gpa
            else:
                prediction = "Invalid input"
        except Exception:
            prediction = "Input the number!"

    return render(request, 'attendance_predict.html', {'prediction': prediction})

def get_model():
    global _model
    if _model is None:
        path = os.path.join(settings.BASE_DIR, 'final_app', 'models', 'gpa_drop_model.pkl')
        try:
            _model = joblib.load(path)
        except Exception as e:
            raise RuntimeError(f"Error loading model: {e}")
    return _model

def get_model_metrics():
    global _model_metrics
    if _model_metrics is None:
        path = os.path.join(settings.BASE_DIR, 'final_app', 'models', 'gpa_drop_model_metrics.pkl')
        try:
            _model_metrics = joblib.load(path)
            if not all(key in _model_metrics for key in ['model_name', 'accuracy', 'precision', 'recall', 'f1_score']):
                raise ValueError("Incomplete metrics file")
        except Exception:
            _model_metrics = {
                'model_name': 'GPA Drop Model',
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0
            }
    return _model_metrics

def home(request):
    return render(request, 'home.html')

def predict_gpa(request):
    model = get_model()
    metrics = get_model_metrics()
    predicted_records = predicted_results = changes = None

    if request.method == 'POST':
        form = GPAPredictionForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            semester_id = form.cleaned_data['semester_id']

            try:
                semester_id = int(semester_id)
            except (ValueError, TypeError):
                semester_id = 1

            previous_records = GPARecord.objects.filter(
                student=student,
                semester_id__lte=semester_id
            ).order_by('semester_id')

            latest_record = previous_records.last()

            if not latest_record:
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
                    prediction = f"Error: {e}"
                    confidence = None

                if previous_records.count() > 1:
                    prev = previous_records[previous_records.count()-2]
                    try:
                        changes = {
                            'grade_change': round(latest_record.avg_grade - prev.avg_grade, 2),
                            'grade_change_pct': round((latest_record.avg_grade - prev.avg_grade) / prev.avg_grade * 100, 1),
                            'attendance_change': round(latest_record.attendance_percentage - prev.attendance_percentage, 2),
                            'attendance_change_pct': round((latest_record.attendance_percentage - prev.attendance_percentage) / prev.attendance_percentage * 100, 1)
                        }
                    except (AttributeError, TypeError, ZeroDivisionError):
                        pass

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
        form = GPAPredictionForm()

    return render(request, 'predict.html', {
        'form': form,
        'predicted_records': predicted_records,
        'prediction': predicted_results,
        'metrics': metrics,
    })

def engagement_ratio(request):
    csv_path = os.path.join(settings.BASE_DIR, 'data', 'processed_student_data.csv')

    # Read all students from CSV
    all_students = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get('name', 'Unknown')
            all_students.append(name)

    all_students = sorted(list(set(all_students)))  # unique sorted names

    selected_students = []
    filtered_data = []

    if request.method == 'POST':
     selected_students = request.POST.getlist('students')  # list of selected names

    # Filter data for selected students
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('name') in selected_students:
                try:
                    row['engagement_ratio'] = float(row.get('engagement_ratio', 0))
                except ValueError:
                    row['engagement_ratio'] = 0
                try:
                    row['risk_score'] = float(row.get('risk_score', 0))
                except ValueError:
                    row['risk_score'] = 0
                
                # Convert semester_id to int if present
                try:
                    row['semester_id'] = int(row.get('semester_id', 0))
                except (ValueError, TypeError):
                    row['semester_id'] = 'N/A'

                filtered_data.append(row)


    context = {
        'all_students': all_students,
        'selected_students': selected_students,
        'filtered_data': filtered_data,
    }
    return render(request, 'engagement_ratio.html', context)


def retrain_model_view(request):
    metrics = None
    if request.method == 'POST':
        try:
            records = GPARecord.objects.all().values()
            df = pd.DataFrame(records)

            X = df[['avg_grade', 'attendance_percentage', 'assessment_count', 'avg_score']]
            y = df['gpa_drop']

            model = RandomForestClassifier()
            model.fit(X, y)

            models_dir = os.path.join(settings.BASE_DIR, 'final_app', 'models')
            os.makedirs(models_dir, exist_ok=True)
            model_path = os.path.join(models_dir, 'gpa_drop_model.pkl')
            joblib.dump(model, model_path)

            report = classification_report(y, model.predict(X), output_dict=True)
            accuracy = round(accuracy_score(y, model.predict(X)) * 100, 2)

            metrics = {
                'model_name': 'Random Forest',
                'accuracy': accuracy,
                'precision': round(report['weighted avg']['precision'] * 100, 2),
                'recall': round(report['weighted avg']['recall'] * 100, 2),
                'f1_score': round(report['weighted avg']['f1-score'] * 100, 2),
            }

            messages.success(request, "✅ Model retrained and saved successfully.")
        except Exception as e:
            messages.error(request, f"❌ Error during retraining: {str(e)}")

        return redirect(reverse('admin:retrain-model'))

    return render(request, 'admin/retrain.html', {
        'metrics': metrics
    })

def recommend_courses(request):
    results = None
    instructor_name = None
    semester_target = None
    error = None
    recommendation_summary = None

    if request.method == 'POST':
        form = CourseRecommendationForm(request.POST)
        if form.is_valid():
            instructor_name = form.cleaned_data['instructor_name']
            latest_semester_id = form.cleaned_data['latest_semester_id']
            semester_target = latest_semester_id + 1
            override_attendance = form.cleaned_data.get('avg_attendance')
            override_assessment = form.cleaned_data.get('avg_assessment_score')

            # Load the trained model
            with open("final_app/models/instructor_course_model.pkl", "rb") as f:
                model = pickle.load(f)

            # First, find instructor_id from instructor_name
            with connection.cursor() as cursor:
                cursor.execute("SELECT instructor_id FROM instructor WHERE instructor_name = %s", [instructor_name])
                row = cursor.fetchone()
                if row:
                    instructor_id = row[0]
                else:
                    error = f"Instructor '{instructor_name}' not found."
                    instructor_id = None

            if instructor_id:
                # Query courses the instructor has taught up to latest_semester_id
                query = """
                SELECT 
                    c.course_id,
                    c.course_name,
                    cd.difficulty_level,
                    AVG(att.attendance_percentage) AS avg_attendance,
                    AVG(a.score) AS avg_assessment_score
                FROM course_instructor ci
                JOIN course c ON ci.course_id = c.course_id
                JOIN course_difficulty cd ON c.course_id = cd.course_id
                JOIN enrollment e ON e.course_id = ci.course_id AND e.semester_id = ci.semester_id
                LEFT JOIN attendance att ON att.enroll_id = e.enroll_id
                LEFT JOIN assessment a ON a.enroll_id = e.enroll_id
                WHERE ci.instructor_id = %s AND ci.semester_id <= %s
                GROUP BY c.course_id, c.course_name, cd.difficulty_level
                """
                df = pd.read_sql_query(query, connection, params=[instructor_id, latest_semester_id])

                if df.empty:
                    error = "No data found for this instructor and semester."
                else:
                    # Override avg_attendance and avg_assessment_score if provided
                    if override_attendance is not None:
                        df['avg_attendance'] = override_attendance
                    if override_assessment is not None:
                        df['avg_assessment_score'] = override_assessment

                    difficulty_map = {'Easy': 0, 'Medium': 1, 'Hard': 2}
                    df['difficulty_level_encoded'] = df['difficulty_level'].map(difficulty_map)

                    X = df[['difficulty_level_encoded', 'avg_attendance', 'avg_assessment_score']]
                    df['predicted_avg_grade'] = model.predict(X)

                    def generate_reason(row):
                        reasons = []
                        if row['predicted_avg_grade'] > 85:
                            reasons.append("High historical grades")
                        if row['avg_attendance'] > 85:
                            reasons.append("High average attendance")
                        if row['difficulty_level'] == 'Hard':
                            reasons.append("Matches course difficulty")
                        if not reasons:
                            return "Recommended based on overall fit"
                        return " & ".join(reasons)

                    df['reason'] = df.apply(generate_reason, axis=1)
                    df = df.sort_values(by='predicted_avg_grade', ascending=False)

                    results = df[['course_id', 'course_name', 'predicted_avg_grade', 'reason']].to_dict(orient='records')

                    # Create a summary recommendation
                    best_course = df.loc[df['predicted_avg_grade'].idxmax()]
                    recommendation_summary = (
                        f"So based on this table, instructor {instructor_name} is best suited for teaching "
                        f"{best_course['course_name']} in the next semester with an expected performance accuracy of "
                        f"{best_course['predicted_avg_grade']:.2f}%."
                    )
            else:
                results = None
        else:
            error = "Invalid form submission."
    else:
        form = CourseRecommendationForm()

    context = {
        'form': form,
        'results': results,
        'instructor_name': instructor_name,
        'semester_target': semester_target,
        'error': error,
        'recommendation_summary': recommendation_summary,
    }
    return render(request, 'recommend_courses.html', context)