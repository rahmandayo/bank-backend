# Import Django's URL routing tools.
from django.urls import include, path

# Import the OpenAPI schema and Swagger UI views.
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Define the central API URL patterns.
urlpatterns = [
    # Include authentication endpoints under the versioned API namespace.
    path("api/v1/auth/", include("users.urls")),

    # Publish the generated OpenAPI schema.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Provide an interactive Swagger UI for API exploration.
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
