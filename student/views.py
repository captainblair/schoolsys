from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from home_auth.notifications import create_notification, notify_admins
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

User = get_user_model()


CLASS_OPTIONS = [
    "LKG",
    "UKG",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
]


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


def _require_login(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return None


def _current_student(request):
    if not _is_student(request.user):
        return None
    return Student.objects.filter(user=request.user).first()


def _select_options(values):
    return [{"value": value, "label": value} for value in values]


def _list_page(request, title, headers, rows, add_url=None, require_admin=False):
    denied = _require_admin(request) if require_admin else _require_login(request)
    if denied:
        return denied
    if not _is_admin(request.user):
        add_url = None
    return render(
        request,
        "students/management-list.html",
        {"title": title, "headers": headers, "rows": rows, "add_url": add_url},
    )


def _form_page(request, title, list_title, list_url, form_title, fields):
    denied = _require_admin(request)
    if denied:
        return denied
    return render(
        request,
        "students/management-form.html",
        {
            "title": title,
            "list_title": list_title,
            "list_url": list_url,
            "form_title": form_title,
            "fields": fields,
        },
    )


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
    fees = Fee.objects.none()
    payments = FeeCollection.objects.none()
    exams = Exam.objects.none()
    timetable_entries = TimeTableEntry.objects.none()
    if student is not None:
        fees = Fee.objects.filter(student_class=student.student_class)
        payments = FeeCollection.objects.select_related("fee").filter(student=student)
        exams = Exam.objects.filter(student_class=student.student_class)
        timetable_entries = TimeTableEntry.objects.select_related("teacher").filter(student_class=student.student_class)
        if student.section:
            timetable_entries = timetable_entries.filter(section__in=["", student.section])
    return render(
        request,
        "students/student-dashboard.html",
        {
            "student": student,
            "fee_count": fees.count(),
            "payment_count": payments.count(),
            "upcoming_exams": exams.order_by("exam_date", "start_time")[:5],
            "timetable_entries": timetable_entries.order_by("day", "start_time")[:5],
            "event_count": Event.objects.count(),
            "book_count": Book.objects.count(),
        },
    )


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


def _student_export_rows():
    students = Student.objects.select_related("parent").order_by("student_id", "first_name", "last_name")
    rows = []
    for student in students:
        rows.append(
            [
                student.student_id,
                f"{student.first_name} {student.last_name}",
                f"{student.student_class} {student.section}".strip(),
                student.date_of_birth.strftime("%Y-%m-%d") if student.date_of_birth else "",
                student.parent.father_name if student.parent_id else "",
                student.parent.mother_name if student.parent_id else "",
                student.mobile_number,
                student.get_approval_status_display(),
                student.parent.present_address if student.parent_id else "",
            ]
        )
    return rows


def _xls_response(headers, rows):
    table_headers = "".join(f"<th>{escape(header)}</th>" for header in headers)
    table_rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>"
        for row in rows
    )
    content = (
        "<html><head><meta charset=\"utf-8\"></head><body>"
        "<table border=\"1\"><thead><tr>"
        f"{table_headers}"
        "</tr></thead><tbody>"
        f"{table_rows}"
        "</tbody></table></body></html>"
    )
    response = HttpResponse(content, content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="students.xls"'
    return response


def _docx_response(headers, rows):
    def cell(value):
        return f"<w:tc><w:p><w:r><w:t>{escape(str(value))}</w:t></w:r></w:p></w:tc>"

    table = "<w:tbl>"
    table += "<w:tr>" + "".join(cell(header) for header in headers) + "</w:tr>"
    for row in rows:
        table += "<w:tr>" + "".join(cell(value) for value in row) + "</w:tr>"
    table += "</w:tbl>"
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>Student List</w:t></w:r></w:p>"
        f"{table}"
        "<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = 'attachment; filename="students.docx"'
    return response


def _pdf_response(headers, rows):
    def pdf_escape(value):
        return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    lines = ["Student List", " | ".join(headers)]
    for row in rows:
        lines.append(" | ".join(str(value) for value in row))
    text_commands = ["BT", "/F1 9 Tf", "40 790 Td", "12 TL"]
    for line in lines[:58]:
        text_commands.append(f"({pdf_escape(line[:115])}) Tj")
        text_commands.append("T*")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{index} 0 obj\n".encode())
        pdf.write(obj)
        pdf.write(b"\nendobj\n")
    xref_offset = pdf.tell()
    pdf.write(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    )
    response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="students.pdf"'
    return response


def download_students(request, file_format):
    denied = _require_admin(request)
    if denied:
        return denied

    headers = ["ID", "Name", "Class", "DOB", "Father", "Mother", "Mobile", "Status", "Address"]
    rows = _student_export_rows()
    if file_format == "xls":
        return _xls_response(headers, rows)
    if file_format == "docx":
        return _docx_response(headers, rows)
    if file_format == "pdf":
        return _pdf_response(headers, rows)
    raise Http404("Unsupported download format.")


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


def profile_approvals(request):
    denied = _require_admin(request)
    if denied:
        return denied

    pending_students = Student.objects.select_related("user", "parent").filter(approval_status="pending").order_by("-id")
    pending_teachers = Teacher.objects.select_related("user").filter(approval_status="pending").order_by("-id")
    return render(
        request,
        "students/profile-approvals.html",
        {
            "pending_students": pending_students,
            "pending_teachers": pending_teachers,
        },
    )


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


def holiday_list(request):
    holidays = Holiday.objects.all()
    rows = [
        [holiday.holiday_id, holiday.name, holiday.holiday_type, holiday.start_date, holiday.end_date]
        for holiday in holidays
    ]
    return _list_page(request, "Holidays", ["ID", "Holiday Name", "Type", "Start Date", "End Date"], rows, "add_holiday")


def add_holiday(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Holiday.objects.create(
            holiday_id=request.POST.get("holiday_id"),
            name=request.POST.get("name"),
            holiday_type=request.POST.get("holiday_type"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
        )
        messages.success(request, "Holiday added successfully")
        return redirect("holiday_list")

    fields = [
        {"name": "holiday_id", "label": "Holiday ID", "type": "text", "required": True},
        {"name": "name", "label": "Holiday Name", "type": "text", "required": True},
        {"name": "holiday_type", "label": "Type of Holiday", "type": "text", "required": True},
        {"name": "start_date", "label": "Start Date", "type": "date", "required": True},
        {"name": "end_date", "label": "End Date", "type": "date", "required": True},
    ]
    return _form_page(request, "Add Holiday", "Holidays", "holiday_list", "Holiday Information", fields)


def fee_list(request):
    fees = Fee.objects.all()
    student = _current_student(request)
    if student is not None:
        fees = fees.filter(student_class=student.student_class)
    rows = [[fee.fee_id, fee.name, fee.student_class, fee.amount, fee.start_date, fee.end_date] for fee in fees]
    return _list_page(request, "Fees", ["ID", "Fees Name", "Class", "Amount", "Start Date", "End Date"], rows, "add_fee")


def add_fee(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Fee.objects.create(
            fee_id=request.POST.get("fee_id"),
            name=request.POST.get("name"),
            student_class=request.POST.get("student_class"),
            amount=request.POST.get("amount"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
        )
        messages.success(request, "Fee added successfully")
        return redirect("fee_list")

    fields = [
        {"name": "fee_id", "label": "Fees ID", "type": "text", "required": True},
        {"name": "name", "label": "Fees Name", "type": "text", "required": True},
        {"name": "student_class", "label": "Class", "type": "select", "required": True, "options": _select_options(CLASS_OPTIONS)},
        {"name": "amount", "label": "Fees Amount", "type": "number", "required": True},
        {"name": "start_date", "label": "Start Date", "type": "date", "required": True},
        {"name": "end_date", "label": "End Date", "type": "date", "required": True},
    ]
    return _form_page(request, "Add Fees", "Fees", "fee_list", "Fees Information", fields)


def fee_collection_list(request):
    collections = FeeCollection.objects.select_related("student", "fee")
    student = _current_student(request)
    if student is not None:
        collections = collections.filter(student=student)
    elif not _is_admin(request.user):
        collections = collections.none()
    rows = [
        [item.receipt_number, item.student, item.fee or "-", item.amount_paid, item.payment_date, item.get_status_display()]
        for item in collections
    ]
    return _list_page(
        request,
        "Fees Collections",
        ["Receipt", "Student", "Fee", "Amount Paid", "Payment Date", "Status"],
        rows,
        "add_fee_collection",
    )


def add_fee_collection(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        FeeCollection.objects.create(
            receipt_number=request.POST.get("receipt_number"),
            student_id=request.POST.get("student"),
            fee_id=request.POST.get("fee") or None,
            amount_paid=request.POST.get("amount_paid"),
            payment_date=request.POST.get("payment_date"),
            status=request.POST.get("status"),
        )
        messages.success(request, "Fee collection added successfully")
        return redirect("fee_collection_list")

    fields = [
        {"name": "receipt_number", "label": "Receipt Number", "type": "text", "required": True},
        {
            "name": "student",
            "label": "Student",
            "type": "select",
            "required": True,
            "options": [{"value": student.id, "label": str(student)} for student in Student.objects.all()],
        },
        {
            "name": "fee",
            "label": "Fee",
            "type": "select",
            "required": False,
            "options": [{"value": fee.id, "label": str(fee)} for fee in Fee.objects.all()],
        },
        {"name": "amount_paid", "label": "Amount Paid", "type": "number", "required": True},
        {"name": "payment_date", "label": "Payment Date", "type": "date", "required": True},
        {
            "name": "status",
            "label": "Status",
            "type": "select",
            "required": True,
            "options": _select_options(["paid", "partial", "unpaid"]),
        },
    ]
    return _form_page(request, "Add Fee Collection", "Fees Collections", "fee_collection_list", "Payment Information", fields)


def expense_list(request):
    denied = _require_admin(request)
    if denied:
        return denied

    expenses = Expense.objects.all()
    rows = [[expense.expense_id, expense.title, expense.category, expense.amount, expense.expense_date] for expense in expenses]
    return _list_page(request, "Expenses", ["ID", "Title", "Category", "Amount", "Date"], rows, "add_expense", require_admin=True)


def add_expense(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Expense.objects.create(
            expense_id=request.POST.get("expense_id"),
            title=request.POST.get("title"),
            category=request.POST.get("category"),
            amount=request.POST.get("amount"),
            expense_date=request.POST.get("expense_date"),
            description=request.POST.get("description"),
        )
        messages.success(request, "Expense added successfully")
        return redirect("expense_list")

    fields = [
        {"name": "expense_id", "label": "Expense ID", "type": "text", "required": True},
        {"name": "title", "label": "Title", "type": "text", "required": True},
        {"name": "category", "label": "Category", "type": "text", "required": True},
        {"name": "amount", "label": "Amount", "type": "number", "required": True},
        {"name": "expense_date", "label": "Date", "type": "date", "required": True},
        {"name": "description", "label": "Description", "type": "textarea", "required": False},
    ]
    return _form_page(request, "Add Expense", "Expenses", "expense_list", "Expense Information", fields)


def salary_list(request):
    denied = _require_admin(request)
    if denied:
        return denied

    salaries = Salary.objects.select_related("teacher")
    rows = [[salary.salary_id, salary.teacher, salary.amount, salary.salary_month, salary.payment_date, salary.status] for salary in salaries]
    return _list_page(request, "Salary", ["ID", "Teacher", "Amount", "Month", "Payment Date", "Status"], rows, "add_salary", require_admin=True)


def add_salary(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Salary.objects.create(
            salary_id=request.POST.get("salary_id"),
            teacher_id=request.POST.get("teacher"),
            amount=request.POST.get("amount"),
            salary_month=request.POST.get("salary_month"),
            payment_date=request.POST.get("payment_date"),
            status=request.POST.get("status"),
        )
        messages.success(request, "Salary added successfully")
        return redirect("salary_list")

    fields = [
        {"name": "salary_id", "label": "Salary ID", "type": "text", "required": True},
        {
            "name": "teacher",
            "label": "Teacher",
            "type": "select",
            "required": True,
            "options": [{"value": teacher.id, "label": str(teacher)} for teacher in Teacher.objects.all()],
        },
        {"name": "amount", "label": "Amount", "type": "number", "required": True},
        {"name": "salary_month", "label": "Month", "type": "text", "required": True},
        {"name": "payment_date", "label": "Payment Date", "type": "date", "required": True},
        {"name": "status", "label": "Status", "type": "text", "required": True},
    ]
    return _form_page(request, "Add Salary", "Salary", "salary_list", "Salary Information", fields)


def exam_list(request):
    exams = Exam.objects.all()
    student = _current_student(request)
    if student is not None:
        exams = exams.filter(student_class=student.student_class)
    rows = [[exam.name, exam.student_class, exam.subject, exam.start_time, exam.end_time, exam.exam_date, exam.fee] for exam in exams]
    return _list_page(request, "Exams", ["Exam Name", "Class", "Subject", "Start Time", "End Time", "Date", "Fee"], rows, "add_exam")


def add_exam(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Exam.objects.create(
            name=request.POST.get("name"),
            student_class=request.POST.get("student_class"),
            subject=request.POST.get("subject"),
            fee=request.POST.get("fee") or 0,
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
            exam_date=request.POST.get("exam_date"),
        )
        messages.success(request, "Exam added successfully")
        return redirect("exam_list")

    fields = [
        {"name": "name", "label": "Exam Name", "type": "text", "required": True},
        {"name": "student_class", "label": "Class", "type": "select", "required": True, "options": _select_options(CLASS_OPTIONS)},
        {"name": "subject", "label": "Subject", "type": "text", "required": True},
        {"name": "fee", "label": "Fees", "type": "number", "required": False},
        {"name": "start_time", "label": "Start Time", "type": "time", "required": True},
        {"name": "end_time", "label": "End Time", "type": "time", "required": True},
        {"name": "exam_date", "label": "Exam Date", "type": "date", "required": True},
    ]
    return _form_page(request, "Add Exam", "Exams", "exam_list", "Exam Information", fields)


def event_list(request):
    events = Event.objects.all()
    rows = [[event.title, event.event_type, event.start_date, event.end_date, event.description] for event in events]
    return _list_page(request, "Events", ["Title", "Type", "Start Date", "End Date", "Description"], rows, "add_event")


def add_event(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Event.objects.create(
            title=request.POST.get("title"),
            event_type=request.POST.get("event_type"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            description=request.POST.get("description"),
        )
        messages.success(request, "Event added successfully")
        return redirect("event_list")

    fields = [
        {"name": "title", "label": "Event Title", "type": "text", "required": True},
        {"name": "event_type", "label": "Event Type", "type": "text", "required": True},
        {"name": "start_date", "label": "Start Date", "type": "date", "required": True},
        {"name": "end_date", "label": "End Date", "type": "date", "required": True},
        {"name": "description", "label": "Description", "type": "textarea", "required": False},
    ]
    return _form_page(request, "Add Event", "Events", "event_list", "Event Information", fields)


def timetable_list(request):
    entries = TimeTableEntry.objects.select_related("teacher")
    student = _current_student(request)
    if student is not None:
        entries = entries.filter(student_class=student.student_class)
        if student.section:
            entries = entries.filter(section__in=["", student.section])
    rows = [[entry.day, entry.student_class, entry.section, entry.subject, entry.teacher or "-", entry.start_time, entry.end_time] for entry in entries]
    return _list_page(request, "Time Table", ["Day", "Class", "Section", "Subject", "Teacher", "Start", "End"], rows, "add_timetable")


def add_timetable(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        TimeTableEntry.objects.create(
            day=request.POST.get("day"),
            student_class=request.POST.get("student_class"),
            section=request.POST.get("section"),
            subject=request.POST.get("subject"),
            teacher_id=request.POST.get("teacher") or None,
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
        )
        messages.success(request, "Time table entry added successfully")
        return redirect("timetable_list")

    fields = [
        {"name": "day", "label": "Day", "type": "select", "required": True, "options": _select_options(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])},
        {"name": "student_class", "label": "Class", "type": "select", "required": True, "options": _select_options(CLASS_OPTIONS)},
        {"name": "section", "label": "Section", "type": "text", "required": False},
        {"name": "subject", "label": "Subject", "type": "text", "required": True},
        {
            "name": "teacher",
            "label": "Teacher",
            "type": "select",
            "required": False,
            "options": [{"value": teacher.id, "label": str(teacher)} for teacher in Teacher.objects.all()],
        },
        {"name": "start_time", "label": "Start Time", "type": "time", "required": True},
        {"name": "end_time", "label": "End Time", "type": "time", "required": True},
    ]
    return _form_page(request, "Add Time Table", "Time Table", "timetable_list", "Time Table Information", fields)


def library_list(request):
    books = Book.objects.all()
    rows = [[book.book_id, book.title, book.author, book.subject, book.publisher, book.quantity, book.available] for book in books]
    return _list_page(request, "Library", ["ID", "Title", "Author", "Subject", "Publisher", "Qty", "Available"], rows, "add_book")


def add_book(request):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        Book.objects.create(
            book_id=request.POST.get("book_id"),
            title=request.POST.get("title"),
            author=request.POST.get("author"),
            subject=request.POST.get("subject"),
            publisher=request.POST.get("publisher"),
            quantity=request.POST.get("quantity") or 1,
            available=request.POST.get("available") or 1,
        )
        messages.success(request, "Book added successfully")
        return redirect("library_list")

    fields = [
        {"name": "book_id", "label": "Book ID", "type": "text", "required": True},
        {"name": "title", "label": "Book Title", "type": "text", "required": True},
        {"name": "author", "label": "Author", "type": "text", "required": True},
        {"name": "subject", "label": "Subject", "type": "text", "required": False},
        {"name": "publisher", "label": "Publisher", "type": "text", "required": False},
        {"name": "quantity", "label": "Quantity", "type": "number", "required": True},
        {"name": "available", "label": "Available", "type": "number", "required": True},
    ]
    return _form_page(request, "Add Book", "Library", "library_list", "Book Information", fields)
