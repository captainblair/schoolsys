from django.conf import settings
from django.db import models
from django.utils.text import slugify

# Create your models here.

class Parent(models.Model):
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100)
    father_mobile = models.CharField(max_length=100)
    father_email = models.EmailField(max_length=100)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100)
    mother_mobile = models.CharField(max_length=100)
    mother_email = models.EmailField(max_length=100)
    present_address = models.TextField()
    permanent_address = models.TextField()

    def __str__(self):
        return f"{self.father_name} & {self.mother_name}"


class Student(models.Model):
    APPROVAL_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="student_profile",
    )
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default="pending")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=100)

    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )

    date_of_birth = models.DateField()
    student_class = models.CharField(max_length=100)
    religion = models.CharField(max_length=20)
    joining_date = models.DateField()
    mobile_number = models.CharField(max_length=100)
    admission_number = models.CharField(max_length=100)
    section = models.CharField(max_length=15)

    student_image = models.ImageField(upload_to='student/', blank=True)

    parent = models.OneToOneField(Parent, on_delete=models.CASCADE)

    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.first_name} {self.last_name} {self.student_id}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"


class Teacher(models.Model):
    APPROVAL_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="teacher_profile",
    )
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default="pending")
    teacher_id = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )
    date_of_birth = models.DateField()
    mobile = models.CharField(max_length=100)
    joining_date = models.DateField()
    qualification = models.CharField(max_length=150)
    experience = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    teacher_class = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    section = models.CharField(max_length=15, blank=True)
    teacher_image = models.ImageField(upload_to='teacher/', blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name} {self.teacher_id}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.teacher_id})"


class Department(models.Model):
    department_id = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    head_of_department = models.CharField(max_length=150)
    start_date = models.DateField()
    number_of_students = models.PositiveIntegerField(default=0)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name} {self.department_id}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subject(models.Model):
    subject_id = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    subject_class = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name} {self.subject_id}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.subject_class})"
