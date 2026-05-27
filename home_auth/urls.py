from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/<uuid:token>/", views.reset_password_view, name="reset_password"),
    path("logout/", views.logout_view, name="logout"),
    path("error-404/", views.error_404_view, name="error_404"),
    path("login.html", views.login_view, name="login-html"),
    path("register.html", views.register_view, name="register-html"),
    path("forgot-password.html", views.forgot_password_view, name="forgot-password-html"),
    path("error-404.html", views.error_404_view, name="error-404-html"),
]
