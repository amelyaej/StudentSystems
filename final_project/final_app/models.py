from django.db import models


class Assessment(models.Model):
    assessment_id = models.AutoField(primary_key=True)
    enroll = models.ForeignKey('Enrollment', models.DO_NOTHING, blank=True, null=True)
    assessment_type = models.CharField(max_length=50)
    score = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'assessment'


class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    enroll = models.ForeignKey('Enrollment', models.DO_NOTHING, blank=True, null=True)
    attendance_percentage = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'attendance'


class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=100)
    dept = models.ForeignKey('Department', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'course'


class CourseDifficulty(models.Model):
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    difficulty_level = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'course_difficulty'


class CourseInstructor(models.Model):
    course_instructor_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    instructor = models.ForeignKey('Instructor', models.DO_NOTHING, blank=True, null=True)
    semester = models.ForeignKey('Semester', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'course_instructor'


class CourseSemester(models.Model):
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    semester = models.ForeignKey('Semester', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'course_semester'


class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'department'


class Enrollment(models.Model):
    enroll_id = models.AutoField(primary_key=True)
    stu = models.ForeignKey('Student', models.DO_NOTHING, blank=True, null=True)
    course = models.ForeignKey(Course, models.DO_NOTHING, blank=True, null=True)
    semester = models.ForeignKey('Semester', models.DO_NOTHING, blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'enrollment'


class Instructor(models.Model):
    instructor_id = models.AutoField(primary_key=True)
    instructor_name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'instructor'


class Semester(models.Model):
    semester_id = models.AutoField(primary_key=True)
    semester_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'semester'


class Student(models.Model):
    stu_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    dob = models.DateField()
    dept = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'student'
