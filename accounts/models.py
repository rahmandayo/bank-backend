# Import UUID generation for non-sequential account identifiers.
import uuid

# Import Django settings to reference the configured customer model.
from django.conf import settings

# Import Django's database model functionality.
from django.db import models


# Define the bank account model.
class Account(models.Model):

    # Define the available bank account categories.
    class AccountType(models.TextChoices):
        CURRENT = "CURRENT", "Current"
        SAVINGS = "SAVINGS", "Savings"

    # Define the permitted account lifecycle states.
    class AccountStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        FROZEN = "FROZEN", "Frozen"
        DORMANT = "DORMANT", "Dormant"
        CLOSED = "CLOSED", "Closed"

    # Generate a non-sequential internal account identifier.
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Associate the account with its customer.
    # PROTECT prevents accidental deletion of the account owner.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bank_accounts",
    )

    # Store the unique customer-facing account number.
    account_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    # Store the account category.
    account_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
    )

    # Reference the supported account currency.
    currency = models.ForeignKey(
        "reference_data.Currency",
        on_delete=models.PROTECT,
        related_name="accounts",
    )

    # Store the account's current lifecycle status.
    status = models.CharField(
        max_length=10,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
        db_index=True,
    )

    # Record when the account was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Record when the account was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    # Record when the account was closed.
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:

        # Display recently created accounts first.
        ordering = ["-created_at"]

        # Define database-level account constraints.
        constraints = [
            # Prevent closed accounts from having inconsistent timestamps.
            models.CheckConstraint(
                condition=(
                    models.Q(status="CLOSED", closed_at__isnull=False)
                    | (
                        ~models.Q(status="CLOSED")
                        & models.Q(closed_at__isnull=True)
                    )
                ),
                name="account_closed_timestamp_consistent",
            ),

            # Allow only one current account per customer.
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(account_type="CURRENT"),
                name="one_current_account_per_user",
            ),
        ]

        # Define database indexes for common account queries.
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="account_user_status_idx",
            ),
            models.Index(
                fields=["user", "created_at"],
                name="account_user_created_idx",
            ),
        ]

        # Provide a readable representation of the account.
    def __str__(self):
        return f"{self.account_number} - {self.account_type}"
