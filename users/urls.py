# Import Django's URL routing function.
from django.urls import path

# Import the authentication endpoint views.
from .views import (
    CsrfBootstrapView,
    CurrentUserView,
    LoginView,
    LogoutView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
)

# Define the URL patterns owned by the users application.
urlpatterns = [
    # Issue a CSRF token for the browser frontend.
    path("csrf/", CsrfBootstrapView.as_view(), name="auth-csrf"),

    # Register a new customer.
    path("register/", RegisterView.as_view(), name="auth-register"),

    # Confirm a customer's email address.
    path(
        "email/verification/confirm/",
        VerifyEmailView.as_view(),
        name="auth-email-verify",
    ),

    # Resend an email-verification link.
    path(
        "email/verification/resend/",
        ResendVerificationView.as_view(),
        name="auth-email-resend",
    ),

    # Sign in using email and password.
    path("login/", LoginView.as_view(), name="auth-login"),

    # Sign out and invalidate the current session.
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    # Return the authenticated customer's profile.
    path("me/", CurrentUserView.as_view(), name="auth-me"),
]
