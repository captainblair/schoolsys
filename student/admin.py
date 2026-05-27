from django.contrib import admin

from .models import Department, Parent, Student, Subject, Teacher

# Register your models here.


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("father_name", "father_mobile", "mother_name", "mother_mobile")
    search_fields = ("father_name", "father_mobile", "mother_name", "mother_mobile")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "first_name",
        "last_name",
        "gender",
        "student_class",
        "section",
        "admission_number",
    )
    list_filter = ("gender", "student_class", "section")
    search_fields = ("student_id", "first_name", "last_name", "admission_number")
    prepopulated_fields = {"slug": ("first_name", "last_name", "student_id")}


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("teacher_id", "name", "gender", "subject", "teacher_class", "mobile")
    list_filter = ("gender", "subject", "teacher_class")
    search_fields = ("teacher_id", "name", "email", "mobile")
    prepopulated_fields = {"slug": ("name", "teacher_id")}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("department_id", "name", "head_of_department", "start_date", "number_of_students")
    search_fields = ("department_id", "name", "head_of_department")
    prepopulated_fields = {"slug": ("name", "department_id")}


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_id", "name", "subject_class")
    search_fields = ("subject_id", "name", "subject_class")
    prepopulated_fields = {"slug": ("name", "subject_id")}
