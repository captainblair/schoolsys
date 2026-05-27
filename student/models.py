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


class Holiday(models.Model):
    holiday_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    holiday_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["start_date", "name"]

    def __str__(self):
        return self.name


class Fee(models.Model):
    fee_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    student_class = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date", "name"]

    def __str__(self):
        return f"{self.name} - {self.student_class}"


class FeeCollection(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("partial", "Partial"),
        ("unpaid", "Unpaid"),
    ]

    receipt_number = models.CharField(max_length=100, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_collections")
    fee = models.ForeignKey(Fee, on_delete=models.SET_NULL, blank=True, null=True, related_name="collections")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="paid")

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.receipt_number} - {self.student}"


class Expense(models.Model):
    expense_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-expense_date"]

    def __str__(self):
        return self.title


class Salary(models.Model):
    salary_id = models.CharField(max_length=100, unique=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="salaries")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    salary_month = models.CharField(max_length=30)
    payment_date = models.DateField()
    status = models.CharField(max_length=50, default="Paid")

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.teacher} - {self.salary_month}"


class Exam(models.Model):
    name = models.CharField(max_length=150)
    student_class = models.CharField(max_length=100)
    subject = models.CharField(max_length=150)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_time = models.TimeField()
    end_time = models.TimeField()
    exam_date = models.DateField()

    class Meta:
        ordering = ["exam_date", "start_time"]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Event(models.Model):
    title = models.CharField(max_length=150)
    event_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["start_date", "title"]

    def __str__(self):
        return self.title


class TimeTableEntry(models.Model):
    day = models.CharField(max_length=20)
    student_class = models.CharField(max_length=100)
    section = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=150)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, blank=True, null=True, related_name="time_table_entries")
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day", "start_time"]
        verbose_name_plural = "Time table entries"

    def __str__(self):
        return f"{self.day} {self.subject}"


class Book(models.Model):
    book_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=150)
    subject = models.CharField(max_length=150, blank=True)
    publisher = models.CharField(max_length=150, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    available = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
