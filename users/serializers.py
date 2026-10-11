# Import Django's built-in password validation function.
from django.contrib.auth.password_validation import validate_password

# Import Django's password validation error type.
from django.core.exceptions import ValidationError as DjangoValidationError

# Import Django's helper for generating username-safe text.
from django.utils.text import slugify

# Import Django REST Framework's serializer tools.
from rest_framework import serializers

# Import the custom BMS user model.
from .models import User


# Generate a unique username from the customer's email address.
def generate_unique_username(email):
    # Use the part of the email address before the @ symbol.
    email_prefix = email.split("@", 1)[0]

    # Convert the email prefix into a username-safe value.
    base_username = slugify(email_prefix)[:140] or "customer"

    # Start with the generated base username.
    username = base_username

    # Start a counter in case the username already exists.
    counter = 1

    # Keep searching until the username is available.
    while User.objects.filter(username__iexact=username).exists():
        # Append a numeric suffix while staying within Django's username limit.
        suffix = str(counter)

        # Build the next candidate username.
        username = f"{base_username[:150 - len(suffix) - 1]}_{suffix}"

        # Increment the counter for another attempt.
        counter += 1

    # Return the available username.
    return username


# Define the JSON fields accepted by customer registration.
class RegisterSerializer(serializers.Serializer):
    # Require the customer's first name.
    first_name = serializers.CharField(max_length=150)

    # Require the customer's last name.
    last_name = serializers.CharField(max_length=150)

    # Require an email address.
    email = serializers.EmailField()

    # Accept an optional phone number.
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    # Accept a password without exposing it in responses.
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    # Require the password to be entered twice.
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    # Normalize the email and reject existing accounts.
    def validate_email(self, value):
        # Remove surrounding whitespace and normalize the address.
        email = value.strip().lower()

        # Reject an email address already assigned to a user.
        if User.objects.filter(email__iexact=email).exists():
            # Return a field-level validation error.
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        # Return the normalized email address.
        return email

    # Validate the password confirmation and password policy.
    def validate(self, attrs):
        # Ensure both password entries are identical.
        if attrs["password"] != attrs["password_confirm"]:
            # Attach the validation error to the confirmation field.
            raise serializers.ValidationError(
                {"password_confirm": "The passwords do not match."}
            )

        # Create an unsaved user for password-similarity validation.
        candidate_user = User(
            username=generate_unique_username(attrs["email"]),
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )

        # Apply the password validators configured in Django settings.
        try:
            # Check the new password against the configured policy.
            validate_password(attrs["password"], user=candidate_user)

        # Catch Django's password-validation errors.
        except DjangoValidationError as error:
            # Return the password errors in the API response.
            raise serializers.ValidationError(
                {"password": list(error.messages)}
            ) from error

        # Return all validated registration fields.
        return attrs

    # Create the customer after all validation succeeds.
    def create(self, validated_data):
        # Remove the confirmation field because it is not a model field.
        validated_data.pop("password_confirm")

        # Remove the plaintext password so it can be hashed properly.
        password = validated_data.pop("password")

        # Generate the customer's unique username.
        username = generate_unique_username(validated_data["email"])

        # Build the user without saving the plaintext password.
        user = User(
            username=username,
            email_verified=False,
            **validated_data,
        )

        # Hash the password using Django's configured password hasher.
        user.set_password(password)

        # Save the new customer to PostgreSQL.
        user.save()

        # Return the newly created user instance.
        return user


# Define the fields accepted by the email-verification endpoint.
class EmailVerificationSerializer(serializers.Serializer):
    # Accept the one-time token supplied by the verification link.
    token = serializers.CharField(
        max_length=100,
        trim_whitespace=False,
    )


# Define the email field used by the resend-verification endpoint.
class ResendVerificationSerializer(serializers.Serializer):
    # Require a syntactically valid email address.
    email = serializers.EmailField()


# Define the fields accepted by the sign-in endpoint.
class LoginSerializer(serializers.Serializer):
    # Require the customer's email address.
    email = serializers.EmailField()

    # Require a password and preserve whitespace exactly as entered.
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    # Normalize the email address before looking up the user.
    def validate_email(self, value):
        # Return the normalized address.
        return value.strip().lower()
