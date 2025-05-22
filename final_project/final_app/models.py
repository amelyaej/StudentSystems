from django.db import models

# Creator choices for MLModel
CREATOR_CHOICES = [
    ('Ijlal', 'Ijlal'),
    ('Dadia', 'Dadia'),
    ('Shynny', 'Shynny'),
    ('Amel', 'Amel'),
]

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100)

    def __str__(self):
        return self.dept_name

    class Meta:
        managed = False
        db_table = 'department'


class Student(models.Model):
    stu_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    dob = models.DateField()
    dept = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'student'


class Semester(models.Model):
    semester_id = models.AutoField(primary_key=True)
    semester_name = models.CharField(max_length=100)

    def __str__(self):
        return self.semester_name

    class Meta:
        managed = False
        db_table = 'semester'


class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.course_name

    class Meta:
        managed = False
        db_table = 'course'


class Enrollment(models.Model):
    enroll_id = models.AutoField(primary_key=True)
    stu = models.ForeignKey(Student, models.DO_NOTHING, blank=True, null=True)
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    semester = models.ForeignKey(Semester, models.DO_NOTHING, blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.stu.name} - {self.course.course_name} - {self.semester.semester_name}"

    class Meta:
        managed = False
        db_table = 'enrollment'


class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    enroll = models.ForeignKey(Enrollment, models.DO_NOTHING, blank=True, null=True)
    attendance_percentage = models.IntegerField()

    def __str__(self):
        return f"{self.enroll} - {self.attendance_percentage}%"

    class Meta:
        managed = False
        db_table = 'attendance'


class Assessment(models.Model):
    assessment_id = models.AutoField(primary_key=True)
    enroll = models.ForeignKey(Enrollment, models.DO_NOTHING, blank=True, null=True)
    assessment_type = models.CharField(max_length=50)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.enroll} - {self.assessment_type} - {self.score}"

    class Meta:
        managed = False
        db_table = 'assessment'


class CourseDifficulty(models.Model):
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    difficulty_level = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.course.course_name} - {self.difficulty_level}"

    class Meta:
        managed = False
        db_table = 'course_difficulty'


class Instructor(models.Model):
    instructor_id = models.AutoField(primary_key=True)
    instructor_name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.instructor_name

    class Meta:
        managed = False
        db_table = 'instructor'


class CourseInstructor(models.Model):
    course_instructor_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    instructor = models.ForeignKey(Instructor, models.DO_NOTHING, blank=True, null=True)
    semester = models.ForeignKey(Semester, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return f"{self.course.course_name} - {self.instructor.instructor_name} - {self.semester.semester_name}"

    class Meta:
        managed = False
        db_table = 'course_instructor'


class CourseSemester(models.Model):
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    semester = models.ForeignKey(Semester, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return f"{self.course.course_name} - {self.semester.semester_name}"

    class Meta:
        managed = False
        db_table = 'course_semester'


class GPARecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    avg_grade = models.FloatField()
    attendance_percentage = models.FloatField()
    assessment_count = models.IntegerField()
    avg_score = models.FloatField()
    prev_gpa = models.FloatField()
    gpa_drop = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.name} - {self.semester.semester_name}"

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['student', 'semester']


class MLModel(models.Model):
    MODEL_TYPES = [
        ('classification', 'Classification'),
        ('regression', 'Regression'),
        ('clustering', 'Clustering'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    use_case = models.CharField(max_length=100)
    dataset = models.CharField(max_length=100)
    file_path = models.FileField(upload_to='ml_models/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.CharField(max_length=50, choices=CREATOR_CHOICES, default='Ijlal')

    accuracy = models.FloatField(default=0)
    precision = models.FloatField(default=0)
    recall = models.FloatField(default=0)
    f1_score = models.FloatField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "ML Model"
        verbose_name_plural = "ML Models"
        ordering = ['-created_at']
