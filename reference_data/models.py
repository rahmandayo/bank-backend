# Import Django's database model functionality.
from django.db import models


# Store supported currencies used across BMS financial applications.
class Currency(models.Model):

    # Store the ISO 4217 currency code, such as QAR or USD.
    code = models.CharField(max_length=3, unique=True)

    # Store the full currency name.
    name = models.CharField(max_length=100)

    # Store the number of decimal places used by the currency.
    minor_unit = models.PositiveSmallIntegerField()

    # Determine whether the currency is available for new operations.
    is_active = models.BooleanField(default=True, db_index=True)

    # Record when the currency was created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        # Sort currencies alphabetically by their ISO code.
        ordering = ["code"]

        # Define database-level validation constraints.
        constraints = [
            # Require currency codes to contain exactly three characters.
            models.CheckConstraint(
                condition=models.Q(code__regex=r"^[A-Z]{3}$"),
                name="currency_code_valid_format",
            ),

            # Restrict supported minor units to valid decimal precision.
            models.CheckConstraint(
                condition=models.Q(minor_unit__gte=0, minor_unit__lte=3),
                name="currency_minor_unit_valid",
            ),
        ]

    # Provide a readable representation of each currency.
    def __str__(self):
        return f"{self.code} - {self.name}"
