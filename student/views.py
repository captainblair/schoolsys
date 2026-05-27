from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from home_auth.notifications import create_notification, notify_admins
from .models import Department, Parent, Student, Subject, Teacher

User = get_user_model()


def _user_groups(user):
    if not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def _is_admin(user):
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or getattr(user, "is_admin", False)
        or "admin" in _user_groups(user)
    )


def _is_student(user):
    return user.is_authenticated and (
        getattr(user, "is_student", False)
        or "student" in _user_groups(user)
    )


def _is_teacher(user):
    return user.is_authenticated and (
        getattr(user, "is_teacher", False)
        or "teacher" in _user_groups(user)
    )


def _student_queryset_for(user):
    queryset = Student.objects.select_related("parent", "user")
    if _is_admin(user):
        return queryset.all()
    if _is_student(user):
        return queryset.filter(user=user)
    return queryset.none()


def _teacher_queryset_for(user):
    queryset = Teacher.objects.select_related("user")
    if _is_admin(user):
        return queryset.all()
    if _is_teacher(user):
        return queryset.filter(user=user)
    return queryset.none()


def _require_admin(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not _is_admin(request.user):
        return HttpResponseForbidden("Only administrators can access this page.")
    return None


def _create_student_from_request(request, user=None, approval_status="pending"):
    parent = Parent.objects.create(
        father_name=request.POST.get("father_name"),
        father_occupation=request.POST.get("father_occupation"),
        father_mobile=request.POST.get("father_mobile"),
        father_email=request.POST.get("father_email"),
        mother_name=request.POST.get("mother_name"),
        mother_occupation=request.POST.get("mother_occupation"),
        mother_mobile=request.POST.get("mother_mobile"),
        mother_email=request.POST.get("mother_email"),
        present_address=request.POST.get("present_address"),
        permanent_address=request.POST.get("permanent_address"),
    )

    return Student.objects.create(
        user=user,
        approval_status=approval_status,
        first_name=request.POST.get("first_name"),
        last_name=request.POST.get("last_name"),
        student_id=request.POST.get("student_id"),
        gender=request.POST.get("gender"),
        date_of_birth=request.POST.get("date_of_birth"),
        student_class=request.POST.get("student_class"),
        religion=request.POST.get("religion"),
        joining_date=request.POST.get("joining_date"),
        mobile_number=request.POST.get("mobile_number"),
        admission_number=request.POST.get("admission_number"),
        section=request.POST.get("section"),
        student_image=request.FILES.get("student_image"),
        parent=parent,
    )


def _create_teacher_from_request(request, user=None, approval_status="pending"):
    email = request.POST.get("email")
    return Teacher.objects.create(
        user=user or User.objects.filter(email__iexact=email).first(),
        approval_status=approval_status,
        teacher_id=request.POST.get("teacher_id"),
        name=request.POST.get("name"),
        gender=request.POST.get("gender"),
        date_of_birth=request.POST.get("date_of_birth"),
        mobile=request.POST.get("mobile"),
        joining_date=request.POST.get("joining_date"),
        qualification=request.POST.get("qualification"),
        experience=request.POST.get("experience"),
        username=request.POST.get("username"),
        email=email,
        address=request.POST.get("address"),
        city=request.POST.get("city"),
        state=request.POST.get("state"),
        zip_code=request.POST.get("zip_code"),
        country=request.POST.get("country"),
        teacher_class=request.POST.get("teacher_class"),
        subject=request.POST.get("subject"),
        section=request.POST.get("section"),
        teacher_image=request.FILES.get("teacher_image"),
    )


def _approve_profile(profile, request, dashboard_name):
    profile.approval_status = "approved"
    profile.save(update_fields=["approval_status"])
    if profile.user:
        create_notification(profile.user, "Profile approved", "Your profile has been approved.", reverse(dashboard_name))


def _reject_profile(profile, request, dashboard_name):
    profile.approval_status = "rejected"
    profile.save(update_fields=["approval_status"])
    if profile.user:
        create_notification(profile.user, "Profile rejected", "Your profile was rejected. Please contact the administrator.", reverse(dashboard_name))


def students(request):
    return student_list(request)


@login_required
def student_dashboard(request):
    student = _student_queryset_for(request.user).first()
    if _is_student(request.user) and student is None:
        return redirect("complete_student_profile")
    return render(request, "students/student-dashboard.html", {"student": student})


@login_required
def teacher_dashboard(request):
    teacher = _teacher_queryset_for(request.user).first()
    if _is_teacher(request.user) and teacher is None:
        return redirect("complete_teacher_profile")
    return render(request, "students/teacher-dashboard.html", {"teacher": teacher})


@login_required
def complete_student_profile(request):
    if not _is_student(request.user):
        return HttpResponseForbidden("Only student accounts can complete a student profile.")
    if Student.objects.filter(user=request.user).exists():
        return redirect("student-dashboard")

    if request.method == "POST":
        student = _create_student_from_request(request, user=request.user, approval_status="pending")
        create_notification(request.user, "Profile submitted", "Your student profile is waiting for admin approval.", reverse("student-dashboard"))
        notify_admins("Student profile pending", f"{student.first_name} {student.last_name} submitted a profile for approval.", reverse("student_list"))
        messages.success(request, "Your profile has been submitted for admin approval.")
        return redirect("student-dashboard")

    return render(request, "students/add-student.html")


@login_required
def complete_teacher_profile(request):
    if not _is_teacher(request.user):
        return HttpResponseForbidden("Only teacher accounts can complete a teacher profile.")
    if Teacher.objects.filter(user=request.user).exists():
        return redirect("teacher-dashboard")

    if request.method == "POST":
        teacher = _create_teacher_from_request(request, user=request.user, approval_status="pending")
        create_notification(request.user, "Profile submitted", "Your teacher profile is waiting for admin approval.", reverse("teacher-dashboard"))
        notify_admins("Teacher profile pending", f"{teacher.name} submitted a profile for approval.", reverse("teacher_list"))
        messages.success(request, "Your profile has been submitted for admin approval.")
        return redirect("teacher-dashboard")

    return render(request, "students/add-teacher.html")


@login_required
def student_details(request, id=None):
    context = {}
    if id is not None:
        context["student"] = get_object_or_404(_student_queryset_for(request.user), id=id)
    elif _is_student(request.user):
        context["student"] = _student_queryset_for(request.user).first()
    return render(request, "students/student-details.html", context)


def add_student(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        student = _create_student_from_request(request, approval_status="approved")

        create_notification(request.user, "Student added", f"{student.first_name} {student.last_name} was added.", reverse("student_list"))
        notify_admins("Student added", f"{student.first_name} {student.last_name} was added.", reverse("student_list"), exclude_user=request.user)
        messages.success(request, "Student added successfully")
        return redirect("student_list")

    return render(request, "students/add-student.html")


def student_list(request):
    student_list = _student_queryset_for(request.user)
    context = {
        "students": student_list,
    }
    return render(request, "students/students.html", context)


def edit_student(request, id=None, slug=None):
    denied = _require_admin(request)
    if denied:
        return denied

    if id is not None:
        student = get_object_or_404(Student, id=id)
    else:
        student = get_object_or_404(Student, slug=slug)

    parent = student.parent

    if request.method == "POST":

        # student data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        student_id = request.POST.get("student_id")
        gender = request.POST.get("gender")
        date_of_birth = request.POST.get("date_of_birth")
        student_class = request.POST.get("student_class")
        religion = request.POST.get("religion")
        joining_date = request.POST.get("joining_date")
        mobile_number = request.POST.get("mobile_number")
        admission_number = request.POST.get("admission_number")
        section = request.POST.get("section")
        student_image = request.FILES.get("student_image")

        # parent data
        parent.father_name = request.POST.get("father_name")
        parent.father_occupation = request.POST.get("father_occupation")
        parent.father_mobile = request.POST.get("father_mobile")
        parent.father_email = request.POST.get("father_email")
        parent.mother_name = request.POST.get("mother_name")
        parent.mother_occupation = request.POST.get("mother_occupation")
        parent.mother_mobile = request.POST.get("mother_mobile")
        parent.mother_email = request.POST.get("mother_email")
        parent.present_address = request.POST.get("present_address")
        parent.permanent_address = request.POST.get("permanent_address")
        parent.save()

        # update student
        student.first_name = first_name
        student.last_name = last_name
        student.student_id = student_id
        student.gender = gender
        student.date_of_birth = date_of_birth
        student.student_class = student_class
        student.religion = religion
        student.joining_date = joining_date
        student.mobile_number = mobile_number
        student.admission_number = admission_number
        student.section = section

        if student_image:
            student.student_image = student_image

        student.save()

        create_notification(request.user, "Student updated", f"{student.first_name} {student.last_name} was updated.", reverse("view_student", args=[student.id]))
        if student.user:
            create_notification(student.user, "Your profile was updated", "Your student profile information was updated.", reverse("student-dashboard"))
        notify_admins("Student updated", f"{student.first_name} {student.last_name} was updated.", reverse("view_student", args=[student.id]), exclude_user=request.user)
        messages.success(request, "Student updated successfully")
        return redirect("student_list")

    context = {
        "student": student,
        "parent": parent,
    }
    return render(request, "students/edit-student.html", context)


def view_student(request, id=None, slug=None):
    if id is not None:
        student = get_object_or_404(_student_queryset_for(request.user), id=id)
    else:
        student = get_object_or_404(_student_queryset_for(request.user), student_id=slug)

    context = {
        "student": student,
    }
    return render(request, "students/student-details.html", context)


def delete_student(request, id=None, slug=None):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        if id is not None:
            student = get_object_or_404(Student, id=id)
        else:
            student = get_object_or_404(Student, slug=slug)

        student_name = f"{student.first_name} {student.last_name}"
        linked_user = student.user
        student.delete()
        create_notification(request.user, "Student deleted", f"{student_name} was deleted.", reverse("student_list"))
        if linked_user:
            create_notification(linked_user, "Student profile deleted", "Your student profile was removed from the system.")
        notify_admins("Student deleted", f"{student_name} was deleted.", reverse("student_list"), exclude_user=request.user)
        messages.success(request, "Student deleted successfully")
        return redirect("student_list")

    return HttpResponseForbidden("Students can only be deleted with a POST request.")


def teacher_list(request):
    teachers = _teacher_queryset_for(request.user)
    return render(request, "students/teachers.html", {"teachers": teachers})


@login_required
def teacher_detail(request, id=None):
    context = {}
    if id is not None:
        context["teacher"] = get_object_or_404(_teacher_queryset_for(request.user), id=id)
    elif _is_teacher(request.user):
        context["teacher"] = _teacher_queryset_for(request.user).first()
    return render(request, "students/teacher-details.html", context)


def add_teacher(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        teacher = _create_teacher_from_request(request, approval_status="approved")
        create_notification(request.user, "Teacher added", f"{teacher.name} was added.", reverse("teacher_detail", args=[teacher.id]))
        if teacher.user:
            create_notification(teacher.user, "Teacher profile linked", "Your teacher profile has been created or linked.", reverse("teacher-dashboard"))
        notify_admins("Teacher added", f"{teacher.name} was added.", reverse("teacher_detail", args=[teacher.id]), exclude_user=request.user)
        messages.success(request, "Teacher added successfully")
        return redirect("teacher_detail", id=teacher.id)

    return render(request, "students/add-teacher.html")


def edit_teacher(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    teacher = get_object_or_404(Teacher, id=id)
    if request.method == "POST":
        teacher.teacher_id = request.POST.get("teacher_id")
        teacher.name = request.POST.get("name")
        teacher.gender = request.POST.get("gender")
        teacher.date_of_birth = request.POST.get("date_of_birth")
        teacher.mobile = request.POST.get("mobile")
        teacher.joining_date = request.POST.get("joining_date")
        teacher.qualification = request.POST.get("qualification")
        teacher.experience = request.POST.get("experience")
        teacher.username = request.POST.get("username")
        teacher.email = request.POST.get("email")
        teacher.user = User.objects.filter(email__iexact=teacher.email).first()
        teacher.address = request.POST.get("address")
        teacher.city = request.POST.get("city")
        teacher.state = request.POST.get("state")
        teacher.zip_code = request.POST.get("zip_code")
        teacher.country = request.POST.get("country")
        teacher.teacher_class = request.POST.get("teacher_class")
        teacher.subject = request.POST.get("subject")
        teacher.section = request.POST.get("section")
        teacher_image = request.FILES.get("teacher_image")
        if teacher_image:
            teacher.teacher_image = teacher_image
        teacher.save()
        create_notification(request.user, "Teacher updated", f"{teacher.name} was updated.", reverse("teacher_detail", args=[teacher.id]))
        if teacher.user:
            create_notification(teacher.user, "Your profile was updated", "Your teacher profile information was updated.", reverse("teacher-dashboard"))
        notify_admins("Teacher updated", f"{teacher.name} was updated.", reverse("teacher_detail", args=[teacher.id]), exclude_user=request.user)
        messages.success(request, "Teacher updated successfully")
        return redirect("teacher_detail", id=teacher.id)

    return render(request, "students/edit-teacher.html", {"teacher": teacher})


def delete_teacher(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method != "POST":
        return HttpResponseForbidden("Teachers can only be deleted with a POST request.")

    teacher = get_object_or_404(Teacher, id=id)
    teacher_name = teacher.name
    linked_user = teacher.user
    teacher.delete()
    create_notification(request.user, "Teacher deleted", f"{teacher_name} was deleted.", reverse("teacher_list"))
    if linked_user:
        create_notification(linked_user, "Teacher profile deleted", "Your teacher profile was removed from the system.")
    notify_admins("Teacher deleted", f"{teacher_name} was deleted.", reverse("teacher_list"), exclude_user=request.user)
    messages.success(request, "Teacher deleted successfully")
    return redirect("teacher_list")


def approve_student(request, id):
    denied = _require_admin(request)
    if denied:
        return denied
    student = get_object_or_404(Student, id=id)
    _approve_profile(student, request, "student-dashboard")
    messages.success(request, "Student profile approved.")
    return redirect("student_list")


def reject_student(request, id):
    denied = _require_admin(request)
    if denied:
        return denied
    student = get_object_or_404(Student, id=id)
    _reject_profile(student, request, "student-dashboard")
    messages.success(request, "Student profile rejected.")
    return redirect("student_list")


def approve_teacher(request, id):
    denied = _require_admin(request)
    if denied:
        return denied
    teacher = get_object_or_404(Teacher, id=id)
    _approve_profile(teacher, request, "teacher-dashboard")
    messages.success(request, "Teacher profile approved.")
    return redirect("teacher_list")


def reject_teacher(request, id):
    denied = _require_admin(request)
    if denied:
        return denied
    teacher = get_object_or_404(Teacher, id=id)
    _reject_profile(teacher, request, "teacher-dashboard")
    messages.success(request, "Teacher profile rejected.")
    return redirect("teacher_list")


def department_list(request):
    denied = _require_admin(request)
    if denied:
        return denied

    departments = Department.objects.all()
    return render(request, "students/departments.html", {"departments": departments})


def add_department(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        department = Department.objects.create(
            department_id=request.POST.get("department_id"),
            name=request.POST.get("name"),
            head_of_department=request.POST.get("head_of_department"),
            start_date=request.POST.get("start_date"),
            number_of_students=request.POST.get("number_of_students") or 0,
        )
        create_notification(request.user, "Department added", f"{department.name} department was added.", reverse("department_list"))
        notify_admins("Department added", f"{department.name} department was added.", reverse("department_list"), exclude_user=request.user)
        messages.success(request, "Department added successfully")
        return redirect("department_list")

    return render(request, "students/add-department.html")


def edit_department(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    department = get_object_or_404(Department, id=id)
    if request.method == "POST":
        department.department_id = request.POST.get("department_id")
        department.name = request.POST.get("name")
        department.head_of_department = request.POST.get("head_of_department")
        department.start_date = request.POST.get("start_date")
        department.number_of_students = request.POST.get("number_of_students") or 0
        department.save()
        create_notification(request.user, "Department updated", f"{department.name} department was updated.", reverse("department_list"))
        notify_admins("Department updated", f"{department.name} department was updated.", reverse("department_list"), exclude_user=request.user)
        messages.success(request, "Department updated successfully")
        return redirect("department_list")

    return render(request, "students/edit-department.html", {"department": department})


def delete_department(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method != "POST":
        return HttpResponseForbidden("Departments can only be deleted with a POST request.")

    department = get_object_or_404(Department, id=id)
    department_name = department.name
    department.delete()
    create_notification(request.user, "Department deleted", f"{department_name} department was deleted.", reverse("department_list"))
    notify_admins("Department deleted", f"{department_name} department was deleted.", reverse("department_list"), exclude_user=request.user)
    messages.success(request, "Department deleted successfully")
    return redirect("department_list")


def subject_list(request):
    denied = _require_admin(request)
    if denied:
        return denied

    subjects = Subject.objects.all()
    return render(request, "students/subjects.html", {"subjects": subjects})


def add_subject(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        subject = Subject.objects.create(
            subject_id=request.POST.get("subject_id"),
            name=request.POST.get("name"),
            subject_class=request.POST.get("subject_class"),
        )
        create_notification(request.user, "Subject added", f"{subject.name} was added.", reverse("subject_list"))
        notify_admins("Subject added", f"{subject.name} was added.", reverse("subject_list"), exclude_user=request.user)
        messages.success(request, "Subject added successfully")
        return redirect("subject_list")

    return render(request, "students/add-subject.html")


def edit_subject(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    subject = get_object_or_404(Subject, id=id)
    if request.method == "POST":
        subject.subject_id = request.POST.get("subject_id")
        subject.name = request.POST.get("name")
        subject.subject_class = request.POST.get("subject_class")
        subject.save()
        create_notification(request.user, "Subject updated", f"{subject.name} was updated.", reverse("subject_list"))
        notify_admins("Subject updated", f"{subject.name} was updated.", reverse("subject_list"), exclude_user=request.user)
        messages.success(request, "Subject updated successfully")
        return redirect("subject_list")

    return render(request, "students/edit-subject.html", {"subject": subject})


def delete_subject(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method != "POST":
        return HttpResponseForbidden("Subjects can only be deleted with a POST request.")

    subject = get_object_or_404(Subject, id=id)
    subject_name = subject.name
    subject.delete()
    create_notification(request.user, "Subject deleted", f"{subject_name} was deleted.", reverse("subject_list"))
    notify_admins("Subject deleted", f"{subject_name} was deleted.", reverse("subject_list"), exclude_user=request.user)
    messages.success(request, "Subject deleted successfully")
    return redirect("subject_list")
