import pandas as pd
import pickle
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = "Predict recommended courses for an instructor in the next semester"

    def add_arguments(self, parser):
        parser.add_argument('--instructor_id', type=int, required=True)
        parser.add_argument('--latest_semester_id', type=int, required=True)

    def handle(self, *args, **options):
        instructor_id = options['instructor_id']
        latest_semester_id = options['latest_semester_id']
        semester_target_id = latest_semester_id + 1  # Next semester

        # --- Load trained model ---
        with open("final_app/models/instructor_course_model.pkl", "rb") as f:
            model = pickle.load(f)

        # --- Fetch relevant data from the database ---
        query = f"""
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
            self.stdout.write(self.style.WARNING("No data found for this instructor and semester."))
            return

        # --- Encode difficulty level ---
        difficulty_map = {'Easy': 0, 'Medium': 1, 'Hard': 2}
        df['difficulty_level_encoded'] = df['difficulty_level'].map(difficulty_map)

        # --- Predict average grades using the model ---
        X = df[['difficulty_level_encoded', 'avg_attendance', 'avg_assessment_score']]
        df['predicted_avg_grade'] = model.predict(X)

        # --- Generate reasons for recommendations ---
        def generate_reason(row):
            reasons = []
            if row['predicted_avg_grade'] > 85:
                reasons.append("High historical grades")
            if row['avg_attendance'] > 85:
                reasons.append("High average attendance")
            if row['difficulty_level'] == 'Hard':
                reasons.append("Matches course difficulty")
            return " & ".join(reasons)

        df['reason'] = df.apply(generate_reason, axis=1)

        # --- Output results ---
        self.stdout.write(self.style.SUCCESS(f"\n📊 Recommended Courses for Instructor ID {instructor_id} in Target Semester ID {semester_target_id}:\n"))
        self.stdout.write(df[['course_id', 'course_name', 'predicted_avg_grade', 'reason']].to_string(index=False))
        