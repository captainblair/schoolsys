from django.contrib import admin

from .models import Parent, Student

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
