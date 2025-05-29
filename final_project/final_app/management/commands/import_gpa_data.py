import os
import pandas as pd
from django.core.management.base import BaseCommand
from final_app.models import Student, GPARecord

class Command(BaseCommand):
    help = 'Import GPA records from cleaned_gpa_data.csv'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Starting GPA data import...")

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(BASE_DIR, 'data', 'cleaned_gpa_data.csv')

 
        if not os.path.exists(csv_path):
            self.stderr.write(f"❌ CSV file not found at {csv_path}")
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            self.stderr.write(f"🚨 Error reading CSV: {e}")
            return

        total_deleted, _ = GPARecord.objects.all().delete()
        if total_deleted > 0:
            self.stdout.write(f"🗑️ Deleted {total_deleted} old GPA records")

        count = 0
        skipped = 0

        for _, row in df.iterrows():
            try:
                student = Student.objects.get(stu_id=row['stu_id'])
            except Student.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ Student with ID {row['stu_id']} does not exist."))
                skipped += 1
                continue

            GPARecord.objects.create(
                student=student,
                semester_id=row['semester_id'],
                avg_grade=row['avg_grade'],
                attendance_percentage=row['attendance_percentage'],
                avg_score=row['avg_score'],
                assessment_count=row['assessment_count'],
                prev_gpa=row['prev_gpa'] if not pd.isna(row['prev_gpa']) else None,
                gpa_drop=bool(row['gpa_drop'])
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully imported {count} GPA records"))
        if skipped > 0:
            self.stdout.write(self.style.NOTICE(f"⚠️ Skipped {skipped} records due to missing students"))