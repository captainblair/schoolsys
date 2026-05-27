from django.contrib import admin

from .models import (
    Book,
    Department,
    Event,
    Exam,
    Expense,
    Fee,
    FeeCollection,
    Holiday,
    Parent,
    Salary,
    Student,
    Subject,
    Teacher,
    TimeTableEntry,
)

# Register your models here.


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("father_name", "father_mobile", "mother_name", "mother_mobile")
    search_fields = ("father_name", "father_mobile", "mother_name", "mother_mobile")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "student_id",
        "first_name",
        "last_name",
        "gender",
        "student_class",
        "section",
        "admission_number",
        "approval_status",
    )
    list_filter = ("approval_status", "gender", "student_class", "section")
    search_fields = ("user__username", "user__email", "student_id", "first_name", "last_name", "admission_number")
    prepopulated_fields = {"slug": ("first_name", "last_name", "student_id")}


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "teacher_id", "name", "gender", "subject", "teacher_class", "mobile", "approval_status")
    list_filter = ("approval_status", "gender", "subject", "teacher_class")
    search_fields = ("user__username", "user__email", "teacher_id", "name", "email", "mobile")
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


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("holiday_id", "name", "holiday_type", "start_date", "end_date")
    search_fields = ("holiday_id", "name", "holiday_type")


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ("fee_id", "name", "student_class", "amount", "start_date", "end_date")
    search_fields = ("fee_id", "name", "student_class")


@admin.register(FeeCollection)
class FeeCollectionAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "student", "fee", "amount_paid", "payment_date", "status")
    list_filter = ("status", "payment_date")
    search_fields = ("receipt_number", "student__first_name", "student__last_name")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("expense_id", "title", "category", "amount", "expense_date")
    list_filter = ("category", "expense_date")
    search_fields = ("expense_id", "title", "category")


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ("salary_id", "teacher", "amount", "salary_month", "payment_date", "status")
    list_filter = ("status", "salary_month")
    search_fields = ("salary_id", "teacher__name")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "student_class", "subject", "exam_date", "start_time", "end_time")
    search_fields = ("name", "student_class", "subject")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "start_date", "end_date")
    search_fields = ("title", "event_type")


@admin.register(TimeTableEntry)
class TimeTableEntryAdmin(admin.ModelAdmin):
    list_display = ("day", "student_class", "section", "subject", "teacher", "start_time", "end_time")
    list_filter = ("day", "student_class", "section")
    search_fields = ("subject", "teacher__name", "student_class")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("book_id", "title", "author", "subject", "quantity", "available")
    search_fields = ("book_id", "title", "author", "subject")
