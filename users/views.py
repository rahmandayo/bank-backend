from django.shortcuts import render

# C# Import hashing and secure random-token utilities.
import hashlib
import logging
import secrets

# Import time utilities for verification-token expiration.
from datetime import timedelta

# Import URL encoding for building the verification link.
from urllib.parse import urlencode

# Import Django settings for the frontend URL and email configuration.
from django.conf import settings

# Import Django authentication functions.
from django.contrib.auth import authenticate, login as django_login, logout as django_logout

# Import Django's email-sending function.
from django.core.mail import send_mail

# Import database transaction and integrity tools.
from django.db import IntegrityError, transaction

# Import the CSRF-token generator.
from django.middleware.csrf import get_token

# Import Django's timezone-aware clock.
from django.utils import timezone

# Import class-based view decorators.
from django.utils.decorators import method_decorator

# Import CSRF decorators for browser-facing POST endpoints.
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

# Import Django REST Framework's permissions and API tools.
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Import the BMS user and verification-token models.
from .models import EmailVerificationToken, User

# Import serializers for the authentication endpoints.
from .serializers import (
    EmailVerificationSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
)


# Create a logger for delivery failures without logging raw tokens.
logger = logging.getLogger(__name__)

# Set the verification-token lifetime to 24 hours.
VERIFICATION_TOKEN_LIFETIME = timedelta(hours=24)


# Return a SHA-256 hash of a verification token.
def hash_verification_token(raw_token):
    # Encode the token and return its hexadecimal SHA-256 digest.
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# Create a new token and invalidate previous unused tokens for this user.
def issue_verification_token(user):
    # Capture the current timezone-aware time.
    now = timezone.now()

    # Invalidate existing unused tokens for this user.
    EmailVerificationToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(used_at=now)

    # Generate a cryptographically random token for the email link.
    raw_token = secrets.token_urlsafe(24)

    # Store only the token hash, never the raw token.
    EmailVerificationToken.objects.create(
        user=user,
        token_hash=hash_verification_token(raw_token),
        expires_at=now + VERIFICATION_TOKEN_LIFETIME,
    )

    # Return the raw token for the email only.
    return raw_token


# Send the verification link using Django's configured default mailer.
def send_verification_email(user, raw_token):
    # Read the frontend base URL, defaulting to the local Vite server.
    frontend_base_url = getattr(
        settings,
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")

    # Encode the token as a query-string parameter.
    query_string = urlencode({"token": raw_token})

    # Build the verification page URL.
    verification_url = f"{frontend_base_url}/verify-email?{query_string}"

    # Define the email subject.
    subject = "Verify your BMS email address"

    # Build a plain-text email containing the verification link.
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        "Please verify your email address using the link below:\n\n"
        f"{verification_url}\n\n"
        "This link expires in 24 hours and can be used only once.\n\n"
        "If you did not create this account, you can ignore this email."
    )

    # Send the email; the current console mailer prints it in the terminal.
    try:
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@bms.local"),
            [user.email],
            fail_silently=False,
        )

    # Record delivery failures without logging the token or email body.
    except Exception:
        # Include only the internal user ID in the error log.
        logger.exception(
            "Verification email delivery failed for user_id=%s",
            user.pk,
        )


# Return a limited profile representation safe for the signed-in customer.
def customer_profile_payload(user):
    # Return profile fields without password hashes or privilege internals.
    return {
        "id": user.pk,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
    }


# Provide a CSRF token to the React frontend.
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfBootstrapView(APIView):
    # Do not require an existing session to obtain the CSRF token.
    authentication_classes = []

    # Permit both anonymous and authenticated browser clients.
    permission_classes = [AllowAny]

    # Handle GET requests for the CSRF token.
    def get(self, request):
        # Generate or retrieve a CSRF token from Django's underlying request.
        csrf_token = get_token(request._request)

        # Return the token so React can send it in the X-CSRFToken header.
        return Response({"csrfToken": csrf_token})


# Create a new customer and issue an email-verification link.
@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    # Do not require the customer to be signed in to register.
    authentication_classes = []

    # Permit anonymous registration requests.
    permission_classes = [AllowAny]

    # Handle POST requests to register a new customer.
    def post(self, request):
        # Validate the registration request against the serializer.
        serializer = RegisterSerializer(data=request.data)

        # Return field-level validation errors for invalid input.
        serializer.is_valid(raise_exception=True)

        # Create the user and token inside a database transaction.
        try:
            # Ensure the customer and token record are committed together.
            with transaction.atomic():
                # Save the new user using the serializer's hashed-password logic.
                user = serializer.save()

                # Generate a raw token and store only its hash.
                raw_token = issue_verification_token(user)

        # Handle a concurrent attempt to register a duplicate unique field.
        except IntegrityError:
            # Return an email conflict rather than an internal server error.
            return Response(
                {
                    "email": [
                        "An account with this email or username already exists."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send the verification email after the database transaction succeeds.
        send_verification_email(user, raw_token)

        # Return a response that does not disclose the raw token.
        return Response(
            {
                "message": (
                    "Account created. Check your email for verification "
                    "instructions. You can request a new link if needed."
                ),
                "email": user.email,
                "email_verified": False,
            },
            status=status.HTTP_201_CREATED,
        )


# Verify an email address using a valid, unused, unexpired token.
@method_decorator(csrf_protect, name="dispatch")
class VerifyEmailView(APIView):
    # Allow verification through a link without an authenticated session.
    authentication_classes = []

    # Permit anonymous verification requests.
    permission_classes = [AllowAny]

    # Handle POST requests to confirm email ownership.
    def post(self, request):
        # Validate the supplied verification token.
        serializer = EmailVerificationSerializer(data=request.data)

        # Return a validation error if the token field is missing or malformed.
        serializer.is_valid(raise_exception=True)

        # Hash the raw token before looking it up in the database.
        token_hash = hash_verification_token(
            serializer.validated_data["token"])

        # Capture the current time for expiry and consumption checks.
        now = timezone.now()

        # Use a transaction to prevent two requests from consuming one token.
        with transaction.atomic():
            # Lock and find a token that is valid and unused.
            token_record = (
                EmailVerificationToken.objects.select_for_update()
                .select_related("user")
                .filter(
                    token_hash=token_hash,
                    used_at__isnull=True,
                    expires_at__gt=now,
                )
                .first()
            )

            # Reject unknown, expired, or previously used tokens.
            if token_record is None:
                # Return a generic token error without revealing account details.
                return Response(
                    {
                        "code": "invalid_or_expired_token",
                        "message": (
                            "This verification link is invalid, expired, "
                            "or has already been used."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the user associated with the valid token.
            user = token_record.user

            # Mark the submitted token as consumed.
            token_record.used_at = now

            # Persist the single-use state.
            token_record.save(update_fields=["used_at"])

            # Mark the user's email address as verified.
            user.email_verified = True

            # Save the verification status and update timestamp.
            user.save(update_fields=["email_verified", "updated_at"])

            # Invalidate other unused verification tokens for the same user.
            EmailVerificationToken.objects.filter(
                user=user,
                used_at__isnull=True,
            ).update(used_at=now)

        # Tell the customer that verification has succeeded.
        return Response(
            {
                "message": "Email verified successfully. You can now sign in.",
                "email_verified": True,
            },
            status=status.HTTP_200_OK,
        )


# Resend a verification link without revealing whether an address is registered.
@method_decorator(csrf_protect, name="dispatch")
class ResendVerificationView(APIView):
    # Resending must also work for a customer who is not signed in.
    authentication_classes = []

    # Permit anonymous resend requests.
    permission_classes = [AllowAny]

    # Handle POST requests to resend the verification email.
    def post(self, request):
        # Validate the email field.
        serializer = ResendVerificationSerializer(data=request.data)

        # Return field errors if the email format is invalid.
        serializer.is_valid(raise_exception=True)

        # Normalize the email address for lookup.
        email = serializer.validated_data["email"].strip().lower()

        # Find an existing, active account that has not verified its email.
        user = User.objects.filter(
            email__iexact=email,
            email_verified=False,
            is_active=True,
        ).first()

        # Only create and send a token when a pending account is found.
        if user is not None:
            # Generate the token and record it atomically.
            with transaction.atomic():
                # Invalidate earlier tokens and issue a new one.
                raw_token = issue_verification_token(user)

            # Send the new verification link.
            send_verification_email(user, raw_token)

        # Use the same response whether the address exists or not.
        return Response(
            {
                "message": (
                    "If an eligible account exists for that email, "
                    "a verification link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


# Authenticate a customer using email and password and create a Django session.
@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    # Require CSRF protection explicitly even for anonymous login requests.
    authentication_classes = []

    # Permit unauthenticated users to submit their credentials.
    permission_classes = [AllowAny]

    # Handle POST requests for sign-in.
    def post(self, request):
        # Validate the email and password fields.
        serializer = LoginSerializer(data=request.data)

        # Reject missing or malformed fields.
        serializer.is_valid(raise_exception=True)

        # Read the normalized email address.
        email = serializer.validated_data["email"]

        # Read the submitted password without modifying its whitespace.
        password = serializer.validated_data["password"]

        # Access the underlying Django HttpRequest for session handling.
        django_request = request._request

        # Locate the account by email address.
        user = User.objects.filter(email__iexact=email).first()

        # Perform a dummy authentication check when no email match exists.
        if user is None:
            # Reduce the difference in processing time for unknown accounts.
            authenticate(django_request, username=email, password=password)

            # Return the same generic credential error.
            return Response(
                {
                    "code": "invalid_credentials",
                    "message": "The supplied email or password is incorrect.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject an incorrect password before disclosing account status.
        if not user.check_password(password):
            # Return the same generic credential error.
            return Response(
                {
                    "code": "invalid_credentials",
                    "message": "The supplied email or password is incorrect.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject accounts disabled by an administrator.
        if not user.is_active:
            # Return a controlled account-disabled response.
            return Response(
                {
                    "code": "account_inactive",
                    "message": "This account is not available for sign-in.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Require email verification before allowing a customer to sign in.
        if not user.email_verified:
            # Tell the customer to verify the registered address.
            return Response(
                {
                    "code": "email_not_verified",
                    "message": "Verify your email address before signing in.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Use Django's configured authentication backend for the final check.
        authenticated_user = authenticate(
            django_request,
            username=user.username,
            password=password,
        )

        # Reject the request if Django's authentication backend refuses it.
        if authenticated_user is None:
            # Return the generic credentials error.
            return Response(
                {
                    "code": "invalid_credentials",
                    "message": "The supplied email or password is incorrect.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create an authenticated server-side Django session.
        django_login(django_request, authenticated_user)

        # Return a limited profile and never return the session identifier in JSON.
        return Response(
            {
                "message": "Signed in successfully.",
                "user": customer_profile_payload(authenticated_user),
            },
            status=status.HTTP_200_OK,
        )


# Return the profile belonging to the currently authenticated session.
class CurrentUserView(APIView):
    # Require a valid Django session for the current-user endpoint.
    permission_classes = [IsAuthenticated]

    # Handle GET requests for the signed-in customer's profile.
    def get(self, request):
        # Use the identity established by Django authentication, not a client ID.
        user = request.user

        # Return only the signed-in customer's profile fields.
        return Response(customer_profile_payload(user), status=status.HTTP_200_OK)


# End the current authenticated Django session.
@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    # Require an authenticated session to log out.
    permission_classes = [IsAuthenticated]

    # Handle POST requests to invalidate the session.
    def post(self, request):
        # Log out using Django's underlying HttpRequest.
        django_logout(request._request)

        # Return no body after the session has been ended.
        return Response(status=status.HTTP_204_NO_CONTENT)
