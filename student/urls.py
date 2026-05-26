from django.urls import path

from . import views

urlpatterns = [
    path("students/", views.students, name="students"),
    path("students.html", views.students, name="students-html"),
    path("student-dashboard.html", views.student_dashboard, name="student-dashboard-html"),
    path("student-details.html", views.student_details, name="student-details-html"),
    path("add-student.html", views.add_student, name="add-student-html"),
    path("edit-student.html", views.edit_student, name="edit-student-html"),
    path("students/dashboard/", views.student_dashboard, name="student-dashboard"),
    path("students/view/", views.student_details, name="student-details"),
    path("students/view/<int:id>/", views.view_student, name="view_student"),
    path("students/add/", views.add_student, name="add-student"),
    path("students/edit/", views.edit_student, name="edit-student"),
    path("students/edit/<int:id>/", views.edit_student, name="edit_student"),
    path("", views.student_list, name="student_list"),
    path("add/", views.add_student, name="add_student")
]
