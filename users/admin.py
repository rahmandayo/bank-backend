# Import Django's administration interface.
from django.contrib import admin

# Import Django's built-in user administration class.
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# Import Django's standard user creation and editing forms.
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

# Import our custom BMS user model.
from .models import User


# Define the form used to create BMS users.
class BMSUserCreationForm(UserCreationForm):

    # Configure the model and fields used by the creation form.
    class Meta(UserCreationForm.Meta):
        # Save users using our custom User model.
        model = User

        # Specify the model fields shown in the creation form.
        fields = ("username", "email", "phone_number")


# Define the form used to edit existing BMS users.
class BMSUserChangeForm(UserChangeForm):

    # Configure the model used by the editing form.
    class Meta:
        # Use our custom User model.
        model = User

        # Make all model fields available to the form.
        fields = "__all__"


# Register our custom User model in Django Admin.
@admin.register(User)
class BMSUserAdmin(DjangoUserAdmin):

    # Use our custom form when editing existing users.
    form = BMSUserChangeForm

    # Use our custom form when creating new users.
    add_form = BMSUserCreationForm

    # Display these columns in the user list.
    list_display = (
        "username",
        "email",
        "phone_number",
        "is_staff",
        "is_active",
        "created_at",
    )

    # Provide filters for account status and privileges.
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
    )

    # Allow administrators to search these fields.
    search_fields = (
        "username",
        "email",
        "phone_number",
        "first_name",
        "last_name",
    )

    # Sort the user list by username.
    ordering = ("username",)

    # Prevent editing login dates and automatic record timestamps.
    readonly_fields = DjangoUserAdmin.readonly_fields + (
        "created_at",
        "updated_at",
    )

    # Define the fields shown when editing an existing user.
    fieldsets = DjangoUserAdmin.fieldsets + (
        # Add the custom phone number field.
        ("Contact information", {"fields": ("phone_number",)}),
        # Display automatic creation and update timestamps.
        ("Record timestamps", {"fields": ("created_at", "updated_at")}),
    )

    # Define the fields shown when creating a new user.
    # Do not inherit Django 6.1's incompatible usable_password field.
    add_fieldsets = (
        # Group all fields needed to create a password-based user.
        (
            None,
            {
                # Use Django Admin's wider form layout.
                "classes": ("wide",),
                # Include the fields defined in our creation form.
                "fields": (
                    "username",
                    "email",
                    "phone_number",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
