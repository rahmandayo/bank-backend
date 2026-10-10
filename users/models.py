# Import Django's settings so the token model can reference the configured User model.
from django.conf import settings

# Import Django's built-in user model base class.
from django.contrib.auth.models import AbstractUser

# Import Django's database model functionality.
from django.db import models


# Define the custom BMS user model using Django's authentication system.
class User(AbstractUser):
    # Store a unique email address for each user.
    email = models.EmailField(unique=True)

    # Store the user's optional phone number.
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Record whether the user has verified ownership of their email address.
    email_verified = models.BooleanField(default=False, db_index=True)

    # Record when the user account was first created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Record when the user account was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    # Define the human-readable representation of a User instance.
    def __str__(self):
        # Return the username when Django displays this user.
        return self.username


# Store verification-token records without storing the original token.
class EmailVerificationToken(models.Model):
    # Associate each token record with the user it verifies.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    # Store the SHA-256 hash of the verification token instead of the raw token.
    token_hash = models.CharField(max_length=64, unique=True)

    # Record when the token was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Record when the token expires.
    expires_at = models.DateTimeField()

    # Record when the token was consumed; NULL means it has not been used.
    used_at = models.DateTimeField(null=True, blank=True)

    # Define the model's default ordering.
    class Meta:
        # Display the most recently created token records first.
        ordering = ["-created_at"]

    # Define the human-readable representation of a token record.
    def __str__(self):
        # Display the associated user ID without exposing the token.
        return f"Email verification record for user {self.user_id}"
